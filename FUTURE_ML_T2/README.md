# Customer Churn Prediction Using XGBoost
This project is focused on predicting customer churn using the XGBoost algorithm, which is well-suited for classification tasks. The dataset used for this project is sourced from Kaggle and includes various features that help determine whether a customer will churn or not.

# Table of Contents
  * Introduction
  * Dataset
  * Installation
  * Usage
  * Model Building
  * Hyperparameter Tuning
  * Results

# Introduction
Customer churn prediction is a crucial aspect of maintaining a customer base, particularly for subscription-based businesses. By predicting which customers are likely to leave, companies can take proactive measures to retain them. In this project, we employ the XGBoost classifier to build a model that predicts customer churn based on historical data.

## Dataset
The dataset used in this project is obtained from Kaggle(https://www.kaggle.com/datasets/ermismbatuhan/digital-marketing-ecommerce-customer-behavior) and contains customer information, including features such as average order value, discount rates, product views, and session details.

   * File: data.csv
   * Number of Columns: 20
   * Target Variable: Churn

## Installation
To run this project, you need to have Python installed along with the necessary libraries. You can install the required dependencies using the following command:

1. Clone the repository:

```bash
git clone https://github.com/Gayathri-Selvaganapathi/customer_churn_prediction.git
cd customer-churn-prediction
pip install -r requirements.txt
```
2. Load the dataset:

Place the data.csv file in the root directory of the project.

3. Run the Jupyter Notebook:

Open the Customer_Churn_Prediction.ipynb file in Jupyter Notebook or JupyterLab and run the cells to build and evaluate the model.

## Model Building

1. Data Preprocessing
    * The dataset initially contains 20 columns, some of which are removed, and others are transformed to be suitable for model training.
    * Columns such as location_code are converted to categorical data.
    * Yes/No fields like credit_card_info_save are converted to binary (0/1) format.
    * Numerical columns with commas are converted to floats for proper mathematical operations.

2. Feature Scaling
    * The numerical features are scaled using Normalizer to ensure that they are on the same scale, improving model performance.

3. Model Training
    * The XGBoost classifier is used to train the model on the processed data.
    * The dataset is split into training and testing sets with a 67-33 ratio.
    * The model is evaluated on the test set, and an accuracy score is calculated.

## Hyperparameter Tuning
Hyperparameter tuning is performed using GridSearchCV to optimize the XGBoost model. Parameters such as max_depth, learning_rate, gamma, and subsample are tuned to improve model performance.

## Results
   * Initial Model Accuracy: 91.54%
   * Final Model Accuracy after Tuning: 92.72%

The final model shows a slight improvement after hyperparameter tuning, demonstrating the importance of fine-tuning model parameters for better performance.



