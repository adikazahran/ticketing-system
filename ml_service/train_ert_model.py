# ticketing_system/ml_service/train_ert_model.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
import joblib
import os

def train_ert_model(data_path_relative='data/synthetic_tickets_data.csv', model_output_path_relative='data/ert_model.pkl'):
    """
    Loads data, preprocesses, trains an ERT model, and saves it.
    Paths are relative to the ml_service directory.
    """
    # Construct absolute paths
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, data_path_relative)
    model_output_path = os.path.join(base_dir, model_output_path_relative)

    # 1. Load Data
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"Error: Dataset not found at {data_path}. Please run generate_data.py first from ml_service directory.")
        return

    # 2. Define Features (X) and Target (y)
    features = ['category', 'priority', 'num_comments', 'is_reopened']
    target = 'resolution_duration_hours'

    X = df[features]
    y = df[target]

    # 3. Preprocessing using ColumnTransformer (for one-hot encoding)
    categorical_features = ['category', 'priority']
    numerical_features = ['num_comments', 'is_reopened'] # is_reopened is boolean, treat as numerical (0/1)

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
            ('num', 'passthrough', numerical_features)
        ],
        remainder='drop' # Drop other columns not in features
    )

    # 4. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Apply preprocessing to training data
    # fit_transform will generate the required column names for later transformation
    X_train_processed = preprocessor.fit_transform(X_train)
    
    # 5. Model Training (RandomForestRegressor)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train_processed, y_train)

    # 6. Evaluation (Optional, but good practice)
    X_test_processed = preprocessor.transform(X_test)
    y_pred = model.predict(X_test_processed)

    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"Model trained successfully!")
    print(f"Mean Absolute Error (MAE): {mae:.2f} hours")
    print(f"R-squared (R2): {r2:.2f}")

    # 7. Save the trained model and preprocessor
    # We save both the model and the preprocessor (ColumnTransformer)
    # because the preprocessor is needed to transform new input data before prediction
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump({'model': model, 'preprocessor': preprocessor, 'features': features}, model_output_path)
    print(f"Model and preprocessor saved to {model_output_path}")

if __name__ == "__main__":
    # Pastikan data/synthetic_tickets_data.csv ada sebelum training
    # Jalankan generate_data.py dari direktori ml_service terlebih dahulu
    train_ert_model()