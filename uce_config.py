model_config  = {
    "model_loc": "./helical/models/uce/model_files/4layer_model.torch",#"./model_files/33l_8ep_1024t_1280.torch",
    "batch_size": 5, #25,
    "pad_length": 1536,
    "pad_token_idx": 0,
    "chrom_token_left_idx": 1,
    "chrom_token_right_idx": 2,
    "cls_token_idx": 3,
    "CHROM_TOKEN_OFFSET": 143574,
    "sample_size": 1024,
    "CXG": True,
    "n_layers": 4,#33,
    "output_dim": 1280,
    "d_hid": 5120,
    "token_dim": 5120,
    "multi_gpu": False
}

files_config = {
    "spec_chrom_csv_path": "./helical/models/uce/model_files/species_chrom.csv",
    "token_file": "./helical/models/uce/model_files/all_tokens.torch",
    "protein_embeddings_dir": "./helical/models/uce/model_files/protein_embeddings/",
    "offset_pkl_path": "./helical/models/uce/model_files/species_offsets.pkl"
}

data_config = {
    "adata_path": "../data/full_cells_macaca_obs_sum_v3.h5ad",
    "dir": "./helical/models/uce/",
    "species": "human", #,'macaca_fascicularis',#"human",
    "filter": False,
    "skip": True
}