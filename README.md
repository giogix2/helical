<div align="center">
  <img src="https://github.com/helicalAI/helical-package/blob/main/assets/logo%2Bname.png" alt="Logo" width="304" height="110">
</div>

## What is Helical ?

Helical provides a framework for and gathers state-of-the-art pre-trained bio foundation models on genomics and transcriptomics modalities.

Helical simplifies the entire application lifecycle when building with bio foundation models. You will be able to:
- Leverage the latest bio foundation models through our easy-to-use python package
- Run example notebooks on key downstream tasks from examples

We will update this repo on a bi-weekly basis with new models, benchmarks, modalities and functions - so stay tuned.
Let’s build the most exciting AI-for-Bio community together!

## Installation

We recommend installing Helical within a conda environment with the commands below (run them in your terminal):
```
conda create --name helical-package python=3.11.8
conda activate helical-package
```
```
pip install --upgrade --force-reinstall git+https://github.com/helicalAI/helical.git
```

We recommend using `Pyhton 3.11.8`.

## Demo & Use Cases

To run examples, be sure to have installed the Helical package (see Installation) and that it is up-to-date.
In you terminal, navigate to the folder of your choice and clone the github repo with the command below:
```
git clone https://github.com/helicalAI/helical.git
```
Within this folder, open the `example` notebook of your choice. We recommend starting with reference_mapping.ipynb

### RNA models:
- reference_mapping.ipynb: Generate embeddingings with geneforme & UCE and compare the outcomes.
- Coming soon: scGPT, SCimilarity, scVI

### DNA models:
- Coming soon: Nucleotide Transformer

# Stuck somewhere ? Other ideas ?
We are eager to help you and interact with you through our slack channel #xxx in the BiB slack. 
You can also open github issues here.

# Why should I use Helical & what to expect in the future?
If you are (or plan to) working with bio foundation models s.a. Geneformer or UCE on RNA and DNA data, Helical will be your best buddy! We provide and improve on:
- Up-to-date model library
- A unified API for all models
- User-facing abstractions tailored to computational biologists, researchers & AI developers
- Innovative use case and application examples and ideas
- Efficient data processing & code-base

We will continuously upload the latest model, publish benchmarks and make our code more efficient.

# Citation
Please use this BibTeX to cite this repository in your publications:
