from helical.services.logger import Logger
from helical.constants.enums import LoggingType, LoggingLevel
import logging
import pickle as pkl
import pandas as pd
import numpy as np
import anndata as ad
from pathlib import Path
import os

BASE_DIR = Path(os.path.dirname(__file__)).parents[0]


META_COLUMN_ORDER = ["sample",
                "snm",
                "project",
                "batch",
                "sex",
                "spid",
                "species",
                "tissue",
                "duration",
                "duration_unit",
                "genetic_material",
                "read_type",
                "strandedness",
                "direction",
                "sid",
                "dose.share",
                "subject",
                ]
class Preprocessor(Logger):
    def __init__(self, loging_type = LoggingType.CONSOLE, level = LoggingLevel.INFO) -> None:
        super().__init__(loging_type, level)
        self.log = logging.getLogger("Preprocessor")

        self.processed_output_path = Path.joinpath(BASE_DIR, "data/full_cells_macaca.h5ad")

    def map_ensbl_to_name(self, input_path: str, mapping_path: str) -> pd.DataFrame:
        '''
        Maps the 'Ensemble ID' to a lowerscore 'Name' via the provided mapping.
        Nan if no mapping is found.

        Args:
            input_path: Path to the ETS csv file.
            mapping_path: Path to the mapping pickle file.
        
        Returns:
            A pandas dataframe representing the gene expression table.
        '''
        mapping = pkl.load(open(mapping_path, 'rb'))
        input = pd.read_csv(input_path)

        self.log.info(f"Starting to do the mapping.")

        input.dropna(subset=['egid'], inplace=True)
        input['gene_name'] = input['egid'].apply(lambda x: mapping[x].get('display_name',np.nan))
        input['gene_name'] = input['gene_name'].apply(lambda x: x.lower() if type(x) is str else x)
        input.dropna(subset=['gene_name'], inplace=True)
        return input
    
    def transform_table(self, input_path: str, mapping_path: str, count_column: str) -> Path:
        '''
        Transform columns to be the features. These can represent genes, proteins
        or genomic regions. Rows represent observations, which are typically cells. 
        
        Args:
            input_path: Path to the ETS csv file.
            mapping_path: Path to the mapping pickle file.
            count_column: string. The name of the column with the counts.
        
        Returns:
            A path to the h5ad processed data.
        '''
        gene_expressions = self.map_ensbl_to_name(input_path, mapping_path)

        self.log.info(f"Successfully received the expression table.")
        self.log.info(f"Converting the expression table to AnnData format.")

        full_df = pd.DataFrame()
        full_obs = pd.DataFrame()
        for _, grouped_expressions in gene_expressions.sort_values(['gene_name']).groupby(['subject','sample']):
            
            # data
            unique_gene_expressions = grouped_expressions.sort_values(['gene_name', count_column]).drop_duplicates(subset='gene_name', keep='last').dropna()
            X = unique_gene_expressions[['gene_name', count_column]].set_index('gene_name').T
            full_df = pd.concat([full_df, X], axis=0)
            
            # metadata
            obs = unique_gene_expressions.drop(columns=['gene_name', 'Unnamed: 0', 'egid', 'rcnt', 'tpm']).drop_duplicates()
            full_obs = pd.concat([full_obs, obs], axis=0)

        adata = ad.AnnData(X = full_df)

        # include observation matrix
        adata.obs = full_obs.reset_index(drop=True)
        adata.obs['subject'] = adata.obs['subject'].astype(str) # necessary for h5py
        adata.obs = adata.obs.reindex(columns=META_COLUMN_ORDER) # optional?: specify order of columns 

        # error in data, 2 and 9 duration should be negative
        adata.obs['duration']= adata.obs[['batch', 'duration']].apply(lambda x: -x[1] if x[1] in [2, 9] and x[0]==1 else x[1], axis=1)
        adata.write_h5ad(self.processed_output_path)

        self.log.info(f"Successfully saved the expression table in AnnData h5ad format: {self.processed_output_path}")
        return self.processed_output_path
