
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.utils import to_categorical
from sklearn.metrics import accuracy_score, precision_score, f1_score, recall_score
from sklearn.model_selection import train_test_split
from helical.benchmark.tasks.base_task import BaseTask
from helical.benchmark.task_models.base_task_model import BaseTaskModel
import numpy as np
import logging
from numpy import ndarray

LOGGER = logging.getLogger(__name__)

class Classifier(BaseTask):
    def __init__(self, labels: list[str], task_model: BaseTaskModel) -> None:
        self.num_types = len(set(labels))

        self.encoder = LabelEncoder()
        self.y_encoded = self.encoder.fit_transform(labels)
        self.y_encoded = to_categorical(self.y_encoded, num_classes=self.num_types)
        self.y_encoded.shape
        
        self.task_model = task_model
        self.trained_models = {}

    def train_task_models(self, x_train: dict[str, ndarray], test_size: float, random_state: int) -> None:
        """Based on the training data x_train, train BaseTaskModels and save them as in a dict as a class variable 'self.tained_models'.
        The training data is split into training and validation data.

        Parameters
        ----------
        x_train : dict[str, ndarray]
            The training data features for each model.
        test_size : float
            The size of the test set.
        random_state : int
            The random state for reproducibility.
        """
        for model_name, x in x_train.items():
            X_train, X_test, y_train, y_test = train_test_split(x, self.y_encoded, test_size=test_size, random_state=random_state)
            
            LOGGER.info(f"Training task model '{model_name}'.")
            self.task_model.compile()
            trained_task_model = self.task_model.train(X_train, y_train, validation_data=(X_test, y_test))
            self.trained_models.update({model_name: trained_task_model}) 
            
    def get_predictions(self, x_eval: dict[str, ndarray]) -> dict[str, ndarray]:
        """Based on the evaluation data, use the trained BaseTaskModels (saved as class variable 'self.tained_models' in a dict) and make predictions.

        Parameters
        ----------
        x_eval : dict[str, ndarray]
            The predictions for each model.
    
        Returns
        -------
        A dictionary containing the predictions for each model.
        """
        predictions = {}
        for model_name, x in x_eval.items():
            m = self.trained_models[model_name]
            
            LOGGER.info(f"Predicting labels for task model '{model_name}'.")
            predictions.update({model_name: m.predict(x)}) 
        return predictions

    def get_evaluations(self, predictions_dict: dict[str, ndarray], eval_labels: ndarray) -> dict[str, dict[str, float]]:
        """Based on the predictions and the ground truth, calculate evaluation metrics: accuracy, precision, f1, recall.
        For the evaluation labels, the same encoder used for the training labels is used.

        Parameters
        ----------
        predictions_dict : dict[str, ndarray]
            The predictions for each model.
        eval_labels : ndarray
            The ground truth labels for the evaluation dataset.

        Returns
        -------
        A dictionary containing the evaluations for each model.
        """
        evaluations = {}

        for model_name, predictions in predictions_dict.items():

            LOGGER.info(f"Evaluating predictions for '{model_name}'.")
            y_pred = np.argmax(predictions, axis=1)
            y_true = self.encoder.fit_transform(eval_labels)
            evaluation = {
                "accuracy": accuracy_score(y_true, y_pred),
                "precision": precision_score(y_true, y_pred, average='macro'),
                "f1": f1_score(y_true, y_pred, average='macro'),
                "recall": recall_score(y_true, y_pred, average='macro'),
            }
            evaluations.update({model_name: evaluation})
        
        return evaluations
