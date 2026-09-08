import os
import json
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from google import genai


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.6-flash"
DB_NAME = "health_app.db"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Food Calorie Estimator",
    page_icon="🥗",
    layout="wide"
)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            height REAL,
            weight REAL,
            activity_level TEXT,
            goal TEXT,
            created_at TEXT
        )
    """)

    # Meal history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            meal_type TEXT,
            food_data TEXT,
            calories REAL,
            protein REAL,
            carbohydrates REAL,
            fat REAL,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Recommendations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Meal plans
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meal_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Shopping lists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# USER AUTHENTICATION
# ============================================================

def register_user(name, email, password):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (name, email, password, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            email,
            password,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

        conn.commit()

        return True, "Account created successfully!"

    except sqlite3.IntegrityError:

        return False, "Email already exists."

    finally:

        conn.close()


def login_user(email, password):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email
        FROM users
        WHERE email = ? AND password = ?
    """, (
        email,
        password
    ))

    user = cursor.fetchone()

    conn.close()

    return user


def get_user(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    conn.close()

    return user


# ============================================================
# PROFILE
# ============================================================

def update_profile(
    user_id,
    age,
    gender,
    height,
    weight,
    activity_level,
    goal
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET age = ?,
            gender = ?,
            height = ?,
            weight = ?,
            activity_level = ?,
            goal = ?
        WHERE id = ?
    """, (
        age,
        gender,
        height,
        weight,
        activity_level,
        goal,
        user_id
    ))

    conn.commit()
    conn.close()


# ============================================================
# AI CLIENT
# ============================================================

def get_ai_client():

    if not API_KEY:

        return None

    return genai.Client(
        api_key=API_KEY
    )


# ============================================================
# FOOD IMAGE ANALYSIS
# ============================================================

def analyze_food_image(
    client,
    image
):

    prompt = """
    Analyze the food shown in this image.

    Identify every visible food item.

    For each food item estimate:

    - Food name
    - Portion size in grams
    - Calories
    - Protein in grams
    - Carbohydrates in grams
    - Fat in grams
    - Fiber in grams
    - Confidence percentage

    Return ONLY valid JSON.

    Use exactly this format:

    {
        "foods": [
            {
                "name": "Food name",
                "portion_grams": 150,
                "calories": 250,
                "protein": 8,
                "carbohydrates": 40,
                "fat": 6,
                "fiber": 3,
                "confidence": 90
            }
        ]
    }

    If no food is detected, return:

    {
        "foods": []
    }

    These are estimates, not laboratory measurements.
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            prompt,
            image
        ]
    )

    text = response.text.strip()

    # Remove markdown JSON formatting if Gemini adds it
    if text.startswith("```"):

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()

    try:

        result = json.loads(text)

        return result

    except json.JSONDecodeError:

        start = text.find("{")
        end = text.rfind("}") + 1

        if start != -1 and end != 0:

            try:

                return json.loads(
                    text[start:end]
                )

            except Exception:

                pass

        return {
            "foods": []
        }


# ============================================================
# SAVE MEAL
# ============================================================

def save_meal(
    user_id,
    meal_type,
    foods,
    calories,
    protein,
    carbohydrates,
    fat
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO meals
        (
            user_id,
            meal_type,
            food_data,
            calories,
            protein,
            carbohydrates,
            fat,
            date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        meal_type,
        json.dumps(foods),
        calories,
        protein,
        carbohydrates,
        fat,
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    conn.commit()
    conn.close()


# ============================================================
# MEAL HISTORY
# ============================================================

def get_meal_history(user_id):

    conn = get_connection()

    query = """
        SELECT
            meal_type,
            calories,
            protein,
            carbohydrates,
            fat,
            date
        FROM meals
        WHERE user_id = ?
        ORDER BY date DESC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(user_id,)
    )

    conn.close()

    return df


# ============================================================
# PERSONALIZED RECOMMENDATIONS
# ============================================================

def generate_recommendations(
    client,
    user,
    meal_history
):

    prompt = f"""
    Provide personalized nutrition recommendations.

    User information:

    Name: {user[1]}
    Age: {user[4]}
    Gender: {user[5]}
    Height: {user[6]} cm
    Weight: {user[7]} kg
    Activity level: {user[8]}
    Goal: {user[9]}

    Recent meal history:

    {meal_history}

    Provide:

    1. Estimated daily calorie target
    2. Protein recommendation
    3. Carbohydrate recommendation
    4. Fat recommendation
    5. Healthy meal suggestions
    6. Foods to include
    7. Foods to limit
    8. General exercise suggestions

    Use clear headings and bullet points.

    State that the recommendations are general
    educational information and not medical advice.
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text


def save_recommendation(
    user_id,
    content
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO recommendations
        (user_id, content, date)
        VALUES (?, ?, ?)
    """, (
        user_id,
        content,
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    conn.commit()
    conn.close()


# ============================================================
# MEAL SUGGESTIONS
# ============================================================

def generate_meal_suggestions(
    client,
    meal_type,
    dietary_preferences,
    calorie_range
):

    preferences = ", ".join(
        dietary_preferences
    )

    if not preferences:

        preferences = "No specific preference"

    prompt = f"""
    Suggest 5 healthy {meal_type} options.

    Dietary preferences:
    {preferences}

    Calorie range:
    {calorie_range[0]} to {calorie_range[1]} kcal

    For every meal provide:

    - Meal name
    - Ingredients
    - Calories
    - Protein
    - Carbohydrates
    - Fat
    - Short preparation method
    - Health benefits

    Use clear headings.
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text


# ============================================================
# 7-DAY MEAL PLAN
# ============================================================

def generate_meal_plan(
    client,
    goal,
    activity_level
):

    prompt = f"""
    Create a practical 7-day healthy meal plan.

    User goal:
    {goal}

    Activity level:
    {activity_level}

    For each day include:

    Breakfast
    Morning snack
    Lunch
    Evening snack
    Dinner

    Include estimated calories for each meal
    and an approximate daily total.

    Make the plan balanced and varied.
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text


def save_meal_plan(
    user_id,
    content
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO meal_plans
        (user_id, content, date)
        VALUES (?, ?, ?)
    """, (
        user_id,
        content,
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    conn.commit()
    conn.close()


# ============================================================
# SHOPPING LIST
# ============================================================

def generate_shopping_list(
    client
):

    prompt = """
    Create a healthy weekly grocery shopping list.

    Organize it into:

    1. Protein
    2. Vegetables
    3. Fruits
    4. Grains and carbohydrates
    5. Dairy
    6. Pantry staples
    7. Healthy snacks

    Include approximate quantities.
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text


def save_shopping_list(
    user_id,
    content
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO shopping_lists
        (user_id, content, date)
        VALUES (?, ?, ?)
    """, (
        user_id,
        content,
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    conn.commit()
    conn.close()


# ============================================================
# AI CHAT
# ============================================================

def ask_ai(
    client,
    user,
    question
):

    prompt = f"""
    You are a friendly nutrition assistant.

    User:
    {user[1]}

    Age:
    {user[4]}

    Goal:
    {user[9]}

    User question:
    {question}

    Give a simple and useful answer.

    Do not diagnose medical conditions.
    Provide general educational information.
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():

    st.title("🥗 Food Calorie Estimator")

    st.subheader(
        "AI-Powered Nutrition Assistant"
    )

    login_tab, signup_tab = st.tabs(
        [
            "Login",
            "Create Account"
        ]
    )

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    with login_tab:

        st.subheader("Login")

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            if not email or not password:

                st.warning(
                    "Please enter email and password."
                )

            else:

                user = login_user(
                    email,
                    password
                )

                if user:

                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.user_name = user[1]

                    st.rerun()

                else:

                    st.error(
                        "Invalid email or password."
                    )

    # --------------------------------------------------------
    # SIGN UP
    # --------------------------------------------------------

    with signup_tab:

        st.subheader(
            "Create Account"
        )

        name = st.text_input(
            "Name",
            key="signup_name"
        )

        email = st.text_input(
            "Email",
            key="signup_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="signup_password"
        )

        if st.button(
            "Create Account",
            use_container_width=True
        ):

            if not name or not email or not password:

                st.warning(
                    "Please fill all fields."
                )

            else:

                success, message = register_user(
                    name,
                    email,
                    password
                )

                if success:

                    st.success(message)

                else:

                    st.error(message)


# ============================================================
# DASHBOARD
# ============================================================

def dashboard_page():

    st.title(
        f"Welcome, {st.session_state.user_name}! 👋"
    )

    st.markdown(
        """
        ### 🥗 Food Calorie Estimator

        Your AI-powered nutrition assistant helps you:

        - 📷 Analyze food images
        - 🔢 Estimate calories
        - 🥩 Track macronutrients
        - 💡 Get personalized recommendations
        - 🍽️ Generate meal suggestions
        - 📅 Create meal plans
        - 🛒 Generate shopping lists
        - 💬 Chat with an AI nutrition assistant
        """
    )

    user_id = st.session_state.user_id

    df = get_meal_history(
        user_id
    )

    if not df.empty:

        total_calories = df["calories"].sum()
        total_protein = df["protein"].sum()
        total_carbs = df["carbohydrates"].sum()
        total_fat = df["fat"].sum()

        st.subheader(
            "📊 Your Meal Summary"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Calories",
            f"{total_calories:.0f} kcal"
        )

        col2.metric(
            "Protein",
            f"{total_protein:.1f} g"
        )

        col3.metric(
            "Carbohydrates",
            f"{total_carbs:.1f} g"
        )

        col4.metric(
            "Fat",
            f"{total_fat:.1f} g"
        )

    else:

        st.info(
            "No meals have been recorded yet. "
            "Go to Calorie Estimator to analyze your first meal."
        )


# ============================================================
# CALORIE ESTIMATOR PAGE
# ============================================================

def calorie_estimator_page(
    client
):

    st.title(
        "📷 Food Calorie Estimator"
    )

    st.write(
        "Upload an image of your food and let AI estimate its nutrition."
    )

    meal_type = st.selectbox(
        "Select Meal Type",
        [
            "Breakfast",
            "Lunch",
            "Dinner",
            "Snack"
        ]
    )

    uploaded_file = st.file_uploader(
        "Upload Food Image",
        type=[
            "jpg",
            "jpeg",
            "png"
        ]
    )

    if uploaded_file:

        image = Image.open(
            uploaded_file
        )

        st.image(
            image,
            caption="Uploaded Food",
            use_container_width=True
        )

        if st.button(
            "🔍 Analyze Food",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                "AI is analyzing your food..."
            ):

                try:

                    result = analyze_food_image(
                        client,
                        image
                    )

                    foods = result.get(
                        "foods",
                        []
                    )

                    if not foods:

                        st.warning(
                            "No food could be detected."
                        )

                        return

                    st.session_state[
                        "food_result"
                    ] = result

                except Exception as error:

                    st.error(
                        f"Analysis failed: {error}"
                    )

        # Display result
        if "food_result" in st.session_state:

            result = st.session_state[
                "food_result"
            ]

            foods = result.get(
                "foods",
                []
            )

            st.subheader(
                "🍽️ Food Analysis"
            )

            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fat = 0

            for food in foods:

                name = food.get(
                    "name",
                    "Unknown food"
                )

                portion = float(
                    food.get(
                        "portion_grams",
                        0
                    )
                    or 0
                )

                calories = float(
                    food.get(
                        "calories",
                        0
                    )
                    or 0
                )

                protein = float(
                    food.get(
                        "protein",
                        0
                    )
                    or 0
                )

                carbs = float(
                    food.get(
                        "carbohydrates",
                        0
                    )
                    or 0
                )

                fat = float(
                    food.get(
                        "fat",
                        0
                    )
                    or 0
                )

                fiber = float(
                    food.get(
                        "fiber",
                        0
                    )
                    or 0
                )

                confidence = food.get(
                    "confidence",
                    0
                )

                st.markdown(
                    f"### 🍴 {name}"
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Portion",
                    f"{portion:.0f} g"
                )

                col2.metric(
                    "Calories",
                    f"{calories:.0f} kcal"
                )

                col3.metric(
                    "Confidence",
                    f"{confidence}%"
                )

                col4, col5, col6 = st.columns(3)

                col4.metric(
                    "Protein",
                    f"{protein:.1f} g"
                )

                col5.metric(
                    "Carbohydrates",
                    f"{carbs:.1f} g"
                )

                col6.metric(
                    "Fat",
                    f"{fat:.1f} g"
                )

                st.write(
                    f"**Fiber:** {fiber:.1f} g"
                )

                st.divider()

                total_calories += calories
                total_protein += protein
                total_carbs += carbs
                total_fat += fat

            st.subheader(
                "📊 Total Nutrition"
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Total Calories",
                f"{total_calories:.0f} kcal"
            )

            col2.metric(
                "Total Protein",
                f"{total_protein:.1f} g"
            )

            col3.metric(
                "Total Carbs",
                f"{total_carbs:.1f} g"
            )

            col4.metric(
                "Total Fat",
                f"{total_fat:.1f} g"
            )

            if st.button(
                "💾 Save Meal",
                use_container_width=True
            ):

                save_meal(
                    st.session_state.user_id,
                    meal_type,
                    foods,
                    total_calories,
                    total_protein,
                    total_carbs,
                    total_fat
                )

                st.success(
                    "Meal saved successfully!"
                )


# ============================================================
# PERSONAL INFORMATION PAGE
# ============================================================

def profile_page():

    st.title(
        "👤 Personal Information"
    )

    user = get_user(
        st.session_state.user_id
    )

    if not user:

        st.error(
            "User profile not found."
        )

        return

    age = st.number_input(
        "Age",
        min_value=1,
        max_value=120,
        value=int(
            user[4] or 20
        )
    )

    gender_options = [
        "Female",
        "Male",
        "Other"
    ]

    current_gender = user[5]

    if current_gender not in gender_options:

        current_gender = "Female"

    gender = st.selectbox(
        "Gender",
        gender_options,
        index=gender_options.index(
            current_gender
        )
    )

    height = st.number_input(
        "Height (cm)",
        min_value=50.0,
        max_value=250.0,
        value=float(
            user[6] or 160
        )
    )

    weight = st.number_input(
        "Weight (kg)",
        min_value=20.0,
        max_value=300.0,
        value=float(
            user[7] or 60
        )
    )

    activity = st.selectbox(
        "Activity Level",
        [
            "Sedentary",
            "Lightly Active",
            "Moderately Active",
            "Very Active",
            "Extremely Active"
        ]
    )

    goal = st.selectbox(
        "Goal",
        [
            "Weight Loss",
            "Weight Gain",
            "Maintenance",
            "Muscle Building"
        ]
    )

    if st.button(
        "💾 Save Profile",
        use_container_width=True
    ):

        update_profile(
            st.session_state.user_id,
            age,
            gender,
            height,
            weight,
            activity,
            goal
        )

        st.success(
            "Profile updated successfully!"
        )


# ============================================================
# RECOMMENDATIONS PAGE
# ============================================================

def recommendations_page(
    client
):

    st.title(
        "💡 Personalized Recommendations"
    )

    user = get_user(
        st.session_state.user_id
    )

    if not user:

        return

    if not user[4]:

        st.warning(
            "Please complete your Personal Information first."
        )

        return

    df = get_meal_history(
        st.session_state.user_id
    )

    if df.empty:

        history_text = (
            "No meals have been recorded yet."
        )

    else:

        history_text = df.to_string(
            index=False
        )

    if st.button(
        "✨ Generate Recommendations",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "Generating personalized recommendations..."
        ):

            recommendations = generate_recommendations(
                client,
                user,
                history_text
            )

        st.markdown(
            recommendations
        )

        save_recommendation(
            st.session_state.user_id,
            recommendations
        )


# ============================================================
# MEAL SUGGESTIONS PAGE
# ============================================================

def meal_suggestions_page(
    client
):

    st.title(
        "🍽️ Meal Suggestions & Planning"
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "Meal Suggestions",
            "7-Day Meal Plan",
            "Shopping List"
        ]
    )

    # --------------------------------------------------------
    # MEAL SUGGESTIONS
    # --------------------------------------------------------

    with tab1:

        meal_type = st.selectbox(
            "Meal Type",
            [
                "Breakfast",
                "Lunch",
                "Dinner",
                "Snack"
            ]
        )

        preferences = st.multiselect(
            "Dietary Preferences",
            [
                "Vegetarian",
                "Vegan",
                "High Protein",
                "Low Carb",
                "Keto",
                "Gluten Free"
            ]
        )

        calorie_range = st.slider(
            "Calorie Range",
            min_value=100,
            max_value=1500,
            value=(300, 600)
        )

        if st.button(
            "🍽️ Generate Meal Suggestions",
            use_container_width=True
        ):

            with st.spinner(
                "Generating meal suggestions..."
            ):

                suggestions = generate_meal_suggestions(
                    client,
                    meal_type,
                    preferences,
                    calorie_range
                )

            st.markdown(
                suggestions
            )

    # --------------------------------------------------------
    # 7-DAY MEAL PLAN
    # --------------------------------------------------------

    with tab2:

        user = get_user(
            st.session_state.user_id
        )

        goal = (
            user[9]
            if user[9]
            else "Maintenance"
        )

        activity = (
            user[8]
            if user[8]
            else "Moderately Active"
        )

        if st.button(
            "📅 Generate 7-Day Meal Plan",
            use_container_width=True
        ):

            with st.spinner(
                "Creating your 7-day meal plan..."
            ):

                plan = generate_meal_plan(
                    client,
                    goal,
                    activity
                )

            st.session_state[
                "meal_plan"
            ] = plan

            st.markdown(
                plan
            )

        if st.session_state.get(
            "meal_plan"
        ):

            if st.button(
                "💾 Save Meal Plan"
            ):

                save_meal_plan(
                    st.session_state.user_id,
                    st.session_state[
                        "meal_plan"
                    ]
                )

                st.success(
                    "Meal plan saved!"
                )

    # --------------------------------------------------------
    # SHOPPING LIST
    # --------------------------------------------------------

    with tab3:

        if st.button(
            "🛒 Generate Shopping List",
            use_container_width=True
        ):

            with st.spinner(
                "Creating shopping list..."
            ):

                shopping_list = generate_shopping_list(
                    client
                )

            st.session_state[
                "shopping_list"
            ] = shopping_list

            st.markdown(
                shopping_list
            )

        if st.session_state.get(
            "shopping_list"
        ):

            if st.button(
                "💾 Save Shopping List"
            ):

                save_shopping_list(
                    st.session_state.user_id,
                    st.session_state[
                        "shopping_list"
                    ]
                )

                st.success(
                    "Shopping list saved!"
                )


# ============================================================
# DAILY TRACKING PAGE
# ============================================================

def tracking_page():

    st.title(
        "📊 Daily Tracking"
    )

    df = get_meal_history(
        st.session_state.user_id
    )

    if df.empty:

        st.info(
            "No meal history available yet."
        )

        return

    st.subheader(
        "Meal History"
    )

    st.dataframe(
        df,
        use_container_width=True
    )

    st.subheader(
        "Calories"
    )

    daily_calories = (
        df.assign(
            date_only=df["date"].str[:10]
        )
        .groupby("date_only")["calories"]
        .sum()
    )

    st.line_chart(
        daily_calories
    )

    st.subheader(
        "Macronutrients"
    )

    daily_macros = (
        df.assign(
            date_only=df["date"].str[:10]
        )
        .groupby("date_only")[
            [
                "protein",
                "carbohydrates",
                "fat"
            ]
        ]
        .sum()
    )

    st.line_chart(
        daily_macros
    )


# ============================================================
# AI CHAT PAGE
# ============================================================

def chat_page(
    client
):

    st.title(
        "🤖 AI Nutrition Assistant"
    )

    user = get_user(
        st.session_state.user_id
    )

    if "chat_history" not in st.session_state:

        st.session_state.chat_history = []

    for message in st.session_state.chat_history:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    question = st.chat_input(
        "Ask a nutrition question..."
    )

    if question:

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question
            }
        )

        with st.chat_message(
            "user"
        ):

            st.markdown(
                question
            )

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "Thinking..."
            ):

                answer = ask_ai(
                    client,
                    user,
                    question
                )

            st.markdown(
                answer
            )

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    initialize_database()

    # --------------------------------------------------------
    # SESSION STATE
    # --------------------------------------------------------

    if "logged_in" not in st.session_state:

        st.session_state.logged_in = False

    if "user_id" not in st.session_state:

        st.session_state.user_id = None

    if "user_name" not in st.session_state:

        st.session_state.user_name = None

    # --------------------------------------------------------
    # API KEY CHECK
    # --------------------------------------------------------

    if not API_KEY:

        st.error(
            "Gemini API key not found."
        )

        st.info(
            "Please check your .env file."
        )

        return

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    if not st.session_state.logged_in:

        login_page()

        return

    # --------------------------------------------------------
    # GEMINI CLIENT
    # --------------------------------------------------------

    try:

        client = get_ai_client()

    except Exception as error:

        st.error(
            f"Gemini initialization failed: {error}"
        )

        return

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    st.sidebar.title(
        "🥗 Food Calorie Estimator"
    )

    st.sidebar.write(
        f"Welcome, {st.session_state.user_name}"
    )

    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Calorie Estimator",
            "Personal Information",
            "Recommendations",
            "Meal Suggestions",
            "Daily Tracking",
            "AI Chat"
        ]
    )

    st.sidebar.divider()

    if st.sidebar.button(
        "Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None

        st.rerun()

    # --------------------------------------------------------
    # PAGE ROUTING
    # --------------------------------------------------------

    if page == "Dashboard":

        dashboard_page()

    elif page == "Calorie Estimator":

        calorie_estimator_page(
            client
        )

    elif page == "Personal Information":

        profile_page()

    elif page == "Recommendations":

        recommendations_page(
            client
        )

    elif page == "Meal Suggestions":

        meal_suggestions_page(
            client
        )

    elif page == "Daily Tracking":

        tracking_page()

    elif page == "AI Chat":

        chat_page(
            client
        )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    main()