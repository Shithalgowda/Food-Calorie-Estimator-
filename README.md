# 🍎 Food Calorie Estimator

## 📌 Overview
Food Calorie Estimator is a Streamlit web application that classifies a food image and estimates its calorie and nutrition information. Users upload a photo of a food item, and the app identifies the food and returns its estimated nutritional breakdown.

## ✨ Features
- 📷 Food image upload
- 🤖 AI-based food classification using a CNN
- 🍽️ Calorie and nutrition estimation
- 📊 Simple, interactive Streamlit interface

## 🛠️ Technologies Used
- **Language:** Python
- **Frontend:** Streamlit
- **AI / Deep Learning:** TensorFlow, Transfer Learning (EfficientNet-based CNN)
- **Database:** SQLite

## ⚙️ How It Works
```
User
  ↓
Upload Food Image
  ↓
CNN Classification (Transfer Learning)
  ↓
Food Identification
  ↓
Calorie & Nutrition Estimation
  ↓
Display Results
```

## 🚀 Installation & Setup

### 1. Clone the repository
```
git clone https://github.com/Shithalgowda/Food-Calorie-Estimator-.git
```

### 2. Navigate to the project folder
```
cd Food-Calorie-Estimator-
```

### 3. Create a virtual environment
```
python -m venv venv
```

### 4. Activate the virtual environment
**Windows:**
```
venv\Scripts\activate
```

### 5. Install the required libraries
```
pip install -r requirements.txt
```

### 6. Run the application
```
streamlit run app.py
```

## 🔮 Future Enhancements
- Improve food recognition accuracy across more food categories
- Add detailed macro breakdown (protein, carbs, fats)
- Deploy the application online

## 👩‍💻 Author
**Keerthana S N**
B.E. Artificial Intelligence & Data Science, K S School of Engineering and Management, Bengaluru

## 📄 License
This project was developed for academic and educational purposes.
