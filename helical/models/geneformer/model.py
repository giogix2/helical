from helical.models.helical import HelicalBaseModel
import logging
from pathlib import Path
import numpy as np
from anndata import AnnData
import os
import pickle
from transformers import BertForMaskedLM
from helical.models.geneformer.geneformer_utils import get_embs,quant_layers
from helical.models.geneformer.geneformer_tokenizer import TranscriptomeTokenizer
from helical.models.geneformer.geneformer_config import GeneformerConfig
from datasets import Dataset
from typing import Optional
from accelerate import Accelerator
import pickle as pkl
from helical.services.downloader import Downloader

class Geneformer(HelicalBaseModel):
    """Geneformer Model. 
    The Geneformer Model is a transformer-based model that can be used to extract gene embeddings from single-cell RNA-seq data. 

    Example
    -------
    >>> from helical.models import Geneformer,GeneformerConfig
    >>> import anndata as ad
    >>> model_config=GeneformerConfig(batch_size=10)
    >>> geneformer = Geneformer(model_config=model_config)
    >>> ann_data = ad.read_h5ad("./data/10k_pbmcs_proc.h5ad")
    >>> dataset = geneformer.process_data(ann_data[:100])
    >>> embeddings = geneformer.get_embeddings(dataset)

    
   
    Parameters
    ----------
    model_dir : str, optional, default = None
        The path to the model directory. None by default, which will download the model if not present.
    model_config : GeneformerConfig, optional, default = default_config
        The model configration

    Returns
    -------
    None

    Notes
    -----
    It has been published in this `Nature Paper <https://www.nature.com/articles/s41586-023-06139-9.epdf?sharing_token=u_5LUGVkd3A8zR-f73lU59RgN0jAjWel9jnR3ZoTv0N2UB4yyXENUK50s6uqjXH69sDxh4Z3J4plYCKlVME-W2WSuRiS96vx6t5ex2-krVDS46JkoVvAvJyWtYXIyj74pDWn_DutZq1oAlDaxfvBpUfSKDdBPJ8SKlTId8uT47M%3D>`_. 
    We use the implementation from the `Geneformer <https://huggingface.co/ctheodoris/Geneformer/tree/main>`_ repository.

    """
    default_config = GeneformerConfig()
    def __init__(self, model_dir: Optional[str] = None, model_config: GeneformerConfig = default_config) -> None:
        super().__init__()
        self.model_config = model_config
        self.downloader = Downloader()

        if model_dir is None:
            self.downloader.download_via_name("geneformer/gene_median_dictionary.pkl")
            self.downloader.download_via_name("geneformer/human_gene_to_ensemble_id.pkl")
            self.downloader.download_via_name("geneformer/token_dictionary.pkl")
            self.downloader.download_via_name("geneformer/geneformer-12L-30M/config.json")
            self.downloader.download_via_name("geneformer/geneformer-12L-30M/pytorch_model.bin")
            self.downloader.download_via_name("geneformer/geneformer-12L-30M/training_args.bin")
            self.model_dir = Path(os.path.join(self.downloader.CACHE_DIR_HELICAL,'geneformer'))
        else:
            self.model_dir = Path(model_dir)

        self.log = logging.getLogger("Geneformer-Model")
        self.device = self.model_config.device

        self.model =  BertForMaskedLM.from_pretrained(self.model_dir / self.model_config.model_name, output_hidden_states=True, output_attentions=False)
        self.model.eval()#.to("cuda:0")
        self.model = self.model.to(self.device)

        self.layer_to_quant = quant_layers(self.model) + self.model_config.emb_layer
        self.emb_mode = self.model_config.emb_mode
        self.forward_batch_size = self.model_config.batch_size
        
        if self.model_config.accelerator:
            self.accelerator = Accelerator(project_dir=self.model_dir, cpu=self.model_config.accelerator["cpu"])
            self.model = self.accelerator.prepare(self.model)
        else:
            self.accelerator = None

    def process_data(self, data: AnnData,  nproc: int = 4,use_gene_symbols=True, output_path: Optional[str] = None) -> Dataset:   
        """Processes the data for the UCE model

        Parameters 
        ----------
        data : AnnData
            The AnnData object containing the data to be processed. It is important to note that the Geneformer uses Ensembl IDs to identify genes.
            The input AnnData object should have a column named 'ensembl_id' or a column with the gene symbols called 'gene_symbols'. 
            Should you use the gene symbols, please set the use_gene_symbols parameter to True.
            Currently the Geneformer only supports human genes.

            If you already have the ensembl_id column, you can skip the mapping step.
        nproc : int, optional, default = 4
            Number of processes to use for dataset processing.
        use_gene_symbols : bool, default = True
            Set this boolean to True if you want to use gene symbols instead of Ensembl IDs. We will map the gene symbols to Ensembl IDs with a mapping taken from the `Ensembl Website <https://www.ensembl.org/`_.
        output_path : str, default = None
            Whether to save the tokenized dataset to the specified output_path.


        Returns
        -------
        Dataset
            The tokenized dataset in the form of a Hugginface Dataset object.
            
        """ 
        files_config = {
            "mapping_path": self.model_dir / "human_gene_to_ensemble_id.pkl",
            "gene_median_path": self.model_dir / "gene_median_dictionary.pkl",
            "token_path": self.model_dir / "token_dictionary.pkl"
        }

        if use_gene_symbols:
            mappings = pkl.load(open(files_config["mapping_path"], 'rb'))
            data.var['ensembl_id'] = data.var['gene_symbols'].apply(lambda x: mappings.get(x,{"id":None})['id'])

        # load token dictionary (Ensembl IDs:token)
        with open(files_config["token_path"], "rb") as f:
            self.gene_token_dict = pickle.load(f)

        self.token_gene_dict = {v: k for k, v in self.gene_token_dict.items()}
        self.pad_token_id = self.gene_token_dict.get("<pad>")

        self.tk = TranscriptomeTokenizer({"cell_type": "cell_type"}, 
                                         nproc=nproc, 
                                         gene_median_file = files_config["gene_median_path"], 
                                         token_dictionary_file = files_config["token_path"])

        tokenized_cells, cell_metadata =  self.tk.tokenize_anndata(data)
        tokenized_dataset = self.tk.create_dataset(tokenized_cells, cell_metadata, use_generator=False)
        
        if output_path:
            output_path = Path(output_path).with_suffix(".dataset")
            tokenized_dataset.save_to_disk(output_path)
        return tokenized_dataset

    def get_embeddings(self, dataset: Dataset) -> np.array:
        """Gets the gene embeddings from the Geneformer model   

        Parameters
        ----------
        dataset : Dataset
            The tokenized dataset containing the processed data

        Returns
        -------
        np.array
            The gene embeddings in the form of a numpy array
        """
        self.log.info(f"Inference started")
        embeddings = get_embs(
            self.model,
            dataset,
            self.emb_mode,
            self.layer_to_quant,
            self.pad_token_id,
            self.forward_batch_size,
            self.device
        )
        print("Done Embeddings",flush=True)
        # return embeddings.cpu().detach().numpy()
        return embeddings.cpu().numpy()