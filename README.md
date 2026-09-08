# 🍎 Food Calorie Estimator

## 📌 Overview

**Food Calorie Estimator** is an AI-based application that helps users estimate the calories present in food items. The system allows users to enter food details manually or upload a food image to identify the food and estimate its calorie content.

The application provides a simple interface for estimating calories and tracking daily food intake.

## 🎯 Objectives

* To estimate the calorie content of food items.
* To identify food items from uploaded images using AI.
* To help users track their daily calorie intake.
* To provide a simple and user-friendly interface for food and calorie management.

## ✨ Features

* 👤 **User Registration & Login**
* 🏠 **Dashboard**
* 🍽️ **Food Calorie Estimation**

  * Manual food entry
  * Food image upload
* 🔍 **Food Database Search**
* 📝 **Meal Logging**
* 📊 **Daily Calorie Tracking**
* 🤖 **AI-based Food Recognition**

## 🛠️ Technologies Used

### Frontend

* Streamlit

### Programming Language

* Python

### AI / Computer Vision

* YOLOv4
* OpenCV
* Darknet

### Database

* SQLite

### Python Libraries

* NumPy
* Pandas
* OpenCV
* Streamlit
* Pillow

## ⚙️ How It Works

```text
User
  ↓
Login / Registration
  ↓
Dashboard
  ↓
Enter Food Details / Upload Food Image
  ↓
AI Food Detection
  ↓
Food Identification
  ↓
Calorie Estimation
  ↓
Log Meal
  ↓
Track Daily Calorie Intake
```

## 📂 Project Structure

```text
food-calorie-estimator/
│
├── app.py
├── health_app.db
├── requirements.txt
├── .gitignore
│
├── food-calorie-estimator/
│   └── ...
│
└── README.md
```

> **Note:** The exact project structure may vary depending on the files included in the repository.

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/Anwesha-1234567/food-calorie-estimator.git
```

### 2. Navigate to the project folder

```bash
cd food-calorie-estimator
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

**Windows:**

```bash
venv\Scripts\activate
```

### 5. Install the required libraries

```bash
pip install -r requirements.txt
```

### 6. Run the application

If the main file is `app.py`:

```bash
streamlit run app.py
```

The application will open in your browser.

## 📸 Application

The application provides an interactive dashboard where users can manage their food information, estimate calories, log meals, and track their daily intake.

## 🔮 Future Enhancements

* Improve food recognition accuracy.
* Add support for more food items.
* Provide personalized diet recommendations.
* Add nutritional information such as protein, carbohydrates, and fats.
* Add graphical reports for weekly and monthly calorie intake.
* Deploy the application online.

## 👩‍💻 Author

**Anwesha Prakash**

AI & Data Science Student
K S School of Engineering and Management, Bengaluru

## 📄 License

This project is developed for educational and academic purposes.
