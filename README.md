# MAIS202 Project: Social Media-Enabled Crisis Informatics

## Overview
This repository contains the source code and implementation for the MAIS202 project. 
The goal of this project is to build a machine learning application focused on **social media-enabled crisis informatics**.

## Dataset
We train our model using earthquake-related tweets from three major seismic events, sourced from the CrisisNLP [dataset](https://crisisnlp.qcri.org/):
- 2013 Pakistan Earthquake
- 2014 California Earthquake
- 2014 Chile Earthquake

Each dataset contains tweet IDs and human-labeled tweets from the corresponding event.

## Features
- Classification of crisis-related information, such as infrastructure damage, casualties, and donation needs.
- Built using Python and machine learning libraries.

## File Structure
- `app.py`: Main application file containing the codebase for data processing and model inference.
- Additional files may include datasets and model scripts.

## Requirements
To run this project, you will need the following:
- Python 3.8 or later
- Required Python libraries:
  - numpy
  - pandas
  - scikit-learn
  - PyTorch
  - transformers
  - seaborn
## References
- Imran, M., Mitra, P., & Castillo, C. (2016). Twitter as a lifeline: Human-annotated Twitter corpora for NLP of crisis-related messages. In Proceedings of the 10th Language Resources and Evaluation Conference (LREC) (pp. 1638–1643). Portorož, Slovenia.
- Nguyen, D. T., Al-Mannai, K. A., Joty, S., Sajjad, H., Imran, M., & Mitra, P. (2017). Robust classification of crisis-related data on social networks using convolutional neural networks. In Proceedings of the 11th International AAAI Conference on Web and Social Media (ICWSM). Montreal, Canada.

## Acknowledgement
Special thanks to the instructors and technical project managers of McGill's Artificial Intelligence Society for their help and support throughout this project.

