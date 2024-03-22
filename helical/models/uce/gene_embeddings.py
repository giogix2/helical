"""
    Helper functions for loading pretrained gene embeddings.
"""

from pathlib import Path
from typing import Dict, Tuple
import torch
from scanpy import AnnData


def get_gene_embedding_paths(embedding_path: Path):
    return {
        'ESM2': {
            'human': embedding_path / 'Homo_sapiens.GRCh38.gene_symbol_to_embedding_ESM2.pt',
            'mouse': embedding_path / 'Mus_musculus.GRCm39.gene_symbol_to_embedding_ESM2.pt',
            'frog': embedding_path / 'Xenopus_tropicalis.Xenopus_tropicalis_v9.1.gene_symbol_to_embedding_ESM2.pt',
            'zebrafish': embedding_path / 'Danio_rerio.GRCz11.gene_symbol_to_embedding_ESM2.pt',
            "mouse_lemur": embedding_path / "Microcebus_murinus.Mmur_3.0.gene_symbol_to_embedding_ESM2.pt",
            "pig": embedding_path / 'Sus_scrofa.Sscrofa11.1.gene_symbol_to_embedding_ESM2.pt',
            "macaca_fascicularis": embedding_path / 'Macaca_fascicularis.Macaca_fascicularis_6.0.gene_symbol_to_embedding_ESM2.pt',
            "macaca_mulatta": embedding_path / 'Macaca_mulatta.Mmul_10.gene_symbol_to_embedding_ESM2.pt',
        }
    }

#TODO Add new function to add embeddings
# extra_species = pd.read_csv("./UCE/model_files/new_species_protein_embeddings.csv").set_index("species").to_dict()["path"]
# MODEL_TO_SPECIES_TO_GENE_EMBEDDING_PATH["ESM2"].update(extra_species) # adds new species


def load_gene_embeddings_adata(adata: AnnData, species: list, embedding_model: str, embeddings_path: Path) -> Tuple[AnnData, 
                                                                                                                   Dict[str, torch.FloatTensor],
                                                                                                                   Dict[str, torch.FloatTensor]]:
    """Loads gene embeddings for all the species/genes in the provided data.

    :param data: An AnnData object containing gene expression data for cells.
    :param species: Species corresponding to this adata
    
    :param embedding_model: The gene embedding model whose embeddings will be loaded.
    :return: A tuple containing:
               - A subset of the data only containing the gene expression for genes with embeddings in all species.
               - A dictionary mapping species name to the corresponding gene embedding matrix (num_genes, embedding_dim).
    """
    # Get species names
    species_names = species
    species_names_set = set(species_names)

    # Get embedding paths for the model
    embedding_paths = get_gene_embedding_paths(embeddings_path)
    species_to_gene_embedding_path = embedding_paths[embedding_model]
    available_species = set(species_to_gene_embedding_path)

    # Ensure embeddings are available for all species
    if not (species_names_set <= available_species):
        raise ValueError(f'The following species do not have gene embeddings: {species_names_set - available_species}')
    # Load gene embeddings for desired species (and convert gene symbols to lower case)
    species_to_gene_symbol_to_embedding = {
        species: {
            gene_symbol.lower(): gene_embedding
            for gene_symbol, gene_embedding in torch.load(species_to_gene_embedding_path[species]).items()
        }
        for species in species_names
    }

    # Determine which genes to include based on gene expression and embedding availability
    genes_with_embeddings = set.intersection(*[
        set(gene_symbol_to_embedding)
        for gene_symbol_to_embedding in species_to_gene_symbol_to_embedding.values()
    ])
    genes_to_use = {gene for gene in adata.var_names if gene.lower() in genes_with_embeddings}
    # Subset data to only use genes with embeddings
    adata = adata[:, adata.var_names.isin(genes_to_use)]
    # Set up dictionary mapping species to gene embedding matrix (num_genes, embedding_dim)
    species_to_gene_embeddings = {
        species_name: torch.stack([
            species_to_gene_symbol_to_embedding[species_name][gene_symbol.lower()]
            for gene_symbol in adata.var_names
        ])
        for species_name in species_names
    }

    return adata, species_to_gene_embeddings, species_to_gene_symbol_to_embedding
