import streamlit as st
import random, os, json, csv, hashlib, base64, calendar
from datetime import datetime
from models import User, Message
from utils import load_challenges, load_quotes, load_badges
import time

# --- Landing Page (shows first) ---
if "show_landing" not in st.session_state:
    st.session_state.show_landing = True

if st.session_state.show_landing:
    img_path = "static/landing_bg.jpg"  # No leading slash!
    if os.path.isfile(img_path):
        with open(img_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        bg_img = f"url('data:image/jpeg;base64,{img_base64}')"
    else:
        # fallback: gradient or color
        bg_img = "linear-gradient(120deg, #171723 30%, #4674d9 100%)"
    st.markdown(f"""
        <style>
        .stApp {{
            background: {bg_img} center center/cover no-repeat !important;
            background-attachment: fixed !important;
        }}
        .landing-bg {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: {bg_img} center center/cover no-repeat !important;
            opacity: 1.0;
            z-index: -2;
        }}
        .landing-overlay {{
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0,0,0,0.55);
            z-index: -1;
        }}
        .landing-title, .landing-tagline, .landing-sub {{
            color: #fff !important;
            text-shadow: 0 2px 8px #000, 0 0 2px #000;
        }}
        .landing-title {{ font-family: 'Montserrat', sans-serif; font-size: 3.5rem; font-weight: 700;
            letter-spacing: 0.2em; margin-top: 2.5em; text-align: center;}}
        .landing-tagline {{ font-size: 2.2rem; font-weight: 600; text-align: center;
            margin-top: 2.5em; letter-spacing: 0.08em;}}
        .landing-sub {{ font-size: 1.1rem; text-align: center; margin-top: 1.5em;}}
        </style>
        <div class="landing-bg"></div>
        <div class="landing-overlay"></div>
        <div class="landing-title">EQUINOX</div>
        <div class="landing-tagline">COMMIT TO SOMETHING</div>
        <div class="landing-sub">Join today and earn back your initiation.</div>
    """, unsafe_allow_html=True)
    join_col = st.columns([2, 1, 2])[1]
    with join_col:
        if st.button("Join Now", key="join_now_btn", use_container_width=True):
            st.session_state.show_landing = False
            st.rerun()
    st.stop()

# --- File paths ---
USERS_FILE = "data/users.json"
CHALLENGES_FILE = "data/exercises.csv"
QUOTES_FILE = "data/quotes.csv"
BADGES_FILE = "data/badges.json"

# --- Utility functions ---
def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()
def load_users():
    if not os.path.exists(USERS_FILE) or os.stat(USERS_FILE).st_size == 0: return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f: return json.load(f)
def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f: json.dump(users, f, indent=2)
def user_to_dict(user, password_hash, role):
    return {
        "username": user.username, "user_id": user.user_id, "role": role,
        "password_hash": password_hash,
        "completed_challenges": list(user.completed_challenges),
        "viewed_calendar": list(user.viewed_calendar),
        "earned_badges": list(user.earned_badges),
        "messages": [m.to_dict() for m in user.messages],
        "avatar": getattr(user, "avatar", None),
        "preferences": getattr(user, "preferences", {}),
    }
def dict_to_user(data):
    user = User(data["username"], data["user_id"])
    user.completed_challenges = set(data.get("completed_challenges", []))
    user.viewed_calendar = set(data.get("viewed_calendar", []))
    user.earned_badges = set(data.get("earned_badges", []))
    user.messages = [Message.from_dict(m) for m in data.get("messages", [])]
    user.avatar = data.get("avatar", None)
    user.preferences = data.get("preferences", {})
    return user
def save_current_user():
    if all(k in st.session_state for k in ["user", "email", "password_hash"]):
        users = load_users()
        users[st.session_state.email] = user_to_dict(
            st.session_state.user, st.session_state.password_hash, st.session_state.role
        )
        save_users(users)
def get_user_rankings():
    users = load_users()
    ranking = [
        {"username": data.get("username", email), "completed": len(data.get("completed_challenges", []))}
        for email, data in users.items() if data.get("role", "Client") == "Client"
    ]
    ranking.sort(key=lambda x: x["completed"], reverse=True)
    return ranking
def get_client_achievements(badges):
    users = load_users()
    client_info = [
        {"username": u["username"], "badges": set(u.get("earned_badges", []))}
        for u in users.values() if u.get("role", "Client") == "Client"
    ]
    badge_names = [badge["name"] for badge in badges]
    return client_info, badge_names
def sign_in(email, password):
    users = load_users()
    if email in users and users[email]["password_hash"] == hash_password(password):
        user = dict_to_user(users[email])
        st.session_state.user = user
        st.session_state.email = email
        st.session_state.password_hash = users[email]["password_hash"]
        st.session_state.role = users[email].get("role", "Client")
        return True
    return False
def sign_up(email, username, password, role):
    users = load_users()
    if email in users: return False
    user = User(username, f"user_{username}")
    password_hash = hash_password(password)
    users[email] = user_to_dict(user, password_hash, role)
    save_users(users)
    return True
def sign_out():
    for k in ["user", "email", "password_hash", "role"]:
        if k in st.session_state: del st.session_state[k]
def load_challenges_file(): return load_challenges(CHALLENGES_FILE)
def load_quotes_file(): return load_quotes(QUOTES_FILE)
def load_badges_file(): return load_badges(BADGES_FILE)

badges = load_badges_file()

# --- App Title ---
st.title(f"EQUINOX" + (f" ({st.session_state['role']})" if "role" in st.session_state else ""))

# --- Authentication ---
if "user" not in st.session_state:
        # Insert background image behind Sign In / Sign Up page
    img_path = "static/landing_bg.jpg"
    if os.path.isfile(img_path):
        with open(img_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        bg_img = f"url('data:image/jpeg;base64,{img_base64}')"
    else:
        bg_img = "linear-gradient(120deg, #171723 30%, #4674d9 100%)"
    st.markdown(f"""
        <style>
        .stApp {{
            background: {bg_img} center center/cover no-repeat !important;
            background-attachment: fixed !important;
        }}
        .landing-bg {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: {bg_img} center center/cover no-repeat !important;
            opacity: 1.0;
            z-index: -2;
        }}
        .landing-overlay {{
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0,0,0,0.55);
            z-index: -1;
        }}
        </style>
        <div class="landing-bg"></div>
        <div class="landing-overlay"></div>
    """, unsafe_allow_html=True)
    st.header("Sign In / Sign Up")
    if st.button("⬅ Back"):
        st.session_state.show_landing = True
        st.rerun()
    # Sidebar Key Benefits
    with st.sidebar:
        st.markdown("""
        <style>
        .key-benefits-box {
            margin-top:2em; padding:1em; border-radius:8px; border:1px solid #cce7ff;
            background-color: var(--secondary-background-color, #f7fafd);
            color: var(--text-color, #222) !important;
        }
        .key-benefits-box h4 {
            color: var(--primary-color, #00c0ff) !important;
            margin-bottom:0.5em;
        }
        @media (prefers-color-scheme: dark) {
            .key-benefits-box {
                background-color: #222 !important;
                color: #eee !important;
            }
            .key-benefits-box h4 {
                color: #00c0ff !important;
            }
        }
        </style>
        <div class="key-benefits-box">
        <h4>Key Benefits</h4>
        <ul style="list-style:none; padding-left:0;">
            <li>✅ Customizable fitness programs</li>
            <li>✅ Generate workouts by level & body part</li>
            <li>✅ Daily progress tracking & motivational quotes</li>
            <li>✅ Achievement badges & leaderboard</li>
            <li>✅ Private coach-client message board</li>
            <li>✅ Helpful health, nutrition and fitness info</li>
            <li>✅ Accessible, visual progress dashboard</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    tab_login, tab_signup = st.tabs(["Sign In", "Sign Up"])
    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Sign In"):
            if sign_in(email.strip().lower(), password):
                st.success(f"Signed in as {email.strip().lower()} ({st.session_state.role})")
                st.rerun()
            else:
                st.error("Invalid email or password.")
    with tab_signup:
        email_new = st.text_input("Email", key="signup_email")
        username_new = st.text_input("Username", key="signup_username")
        password_new = st.text_input("Password", type="password", key="signup_password")
        role_new = st.radio("Sign up as:", ["Client", "Coach"])
        avatar_file_new = st.file_uploader("Upload Profile Avatar (jpg/png)", type=["jpg", "jpeg", "png"], key="signup_avatar")
        if st.button("Sign Up"):
            if not email_new or not username_new or not password_new or not role_new:
                st.warning("Please fill all fields.")
            elif "@" not in email_new or "." not in email_new:
                st.warning("Please enter a valid email address.")
            else:
                avatar_b64 = None
                if avatar_file_new:
                    avatar_bytes = avatar_file_new.read()
                    avatar_b64 = base64.b64encode(avatar_bytes).decode("utf-8")
                users = load_users()
                if email_new.strip().lower() in users:
                    st.error("Email already registered.")
                else:
                    user = User(username_new.strip(), f"user_{username_new.strip()}")
                    password_hash = hash_password(password_new)
                    user.avatar = avatar_b64
                    users[email_new.strip().lower()] = user_to_dict(user, password_hash, role_new)
                    save_users(users)
                    st.success("Account created! Please sign in.")
    st.stop()

# --- Sidebar: Profile & Preferences ---
user = st.session_state.user
role = st.session_state.get("role", "Client")
st.sidebar.header(f"{role} : {user.username}")

# Display avatar below name (no upload here)
if getattr(user, "avatar", None):
    st.sidebar.image(base64.b64decode(user.avatar), width=100, caption="Your Avatar")

st.sidebar.subheader("Account")
username = st.sidebar.text_input("Change Username", user.username)
if st.sidebar.button("Update Username"):
    user.username = username
    st.success(f"Username updated to {username}")
    save_current_user()
st.sidebar.write(f"Current Role: **{role}**")

st.sidebar.subheader("Preferences")
font_size = st.sidebar.selectbox(
    "Font Size", ["small", "medium", "large"],
    index=["small", "medium", "large"].index(user.preferences.get("font_size", "medium"))
)
if st.sidebar.button("Save Preferences"):
    user.preferences = {"font_size": font_size}
    st.success("Preferences saved!")
    save_current_user()
if getattr(user, "preferences", None):
    font_map = {"small": "14px", "medium": "18px", "large": "22px"}
    st.markdown(
        f"""<style>
        html, body, [class*="css"]  {{
            font-size: {font_map.get(user.preferences.get("font_size", "medium"), "18px")} !important;
        }}
        </style>""", unsafe_allow_html=True,
    )
st.sidebar.info("")



# Move Sign Out button to the bottom of the sidebar
st.sidebar.markdown("<hr style='margin:2em 0;'>", unsafe_allow_html=True)
if st.sidebar.button("Sign Out"):
    save_current_user()
    sign_out()
    st.success("Signed out!")
    st.rerun()

# --- Tabs ---
welcome_name = user.username if user.username else "User"
if role == "Coach":
    st.subheader(f"Welcome, {welcome_name}! 🎓")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🏋 Manage Challenges", "🗓 Calendar", "🏆 Achievements", "💬 Messages", "🏅 Leaderboard"]
    )
else:
    st.subheader(f"Welcome, {welcome_name}! 💪")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🏋 Challenges", "🗓 Calendar", "🏆 Badges", "💬 Messages", "🏅 Leaderboard"]
    )

# --- Challenges Tab ---
with tab1:
    if role == "Coach":
        st.header("Create New Workout")
        workout_title = st.text_input("Workout Title")
        workout_desc = st.text_area("Workout Description")
        workout_difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])
        workout_equipment = st.text_input("Equipment")
        workout_body_part = st.text_input("Body Part")
        if st.button("Add Workout"):
            if not workout_title or not workout_desc:
                st.warning("Please fill in all required fields.")
            else:
                # Load existing challenges
                challenges = load_challenges_file()
                # Add new workout
                new_workout = {
                    "title": workout_title,
                    "description": workout_desc,
                    "difficulty": workout_difficulty,
                    "equipment": workout_equipment,
                    "body_part": workout_body_part,
                }
                challenges.append(new_workout)
                # Save to CSV
                with open(CHALLENGES_FILE, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["title", "description", "difficulty", "equipment", "body_part"])
                    writer.writeheader()
                    writer.writerows(challenges)
                st.success("Workout added!")
                st.rerun()
    else:
        challenges = load_challenges_file()
        st.header("Create My Workout Program")
        body_parts = sorted(list({c.get("body_part", "Other").capitalize() for c in challenges}))
        selected_body_part = st.selectbox("Choose Body Part", ["All"] + body_parts)
        filtered_by_body = challenges if selected_body_part == "All" else [
            c for c in challenges if c.get("body_part", "").capitalize() == selected_body_part
        ]
        sel_difficulty = st.selectbox(
            "Choose Difficulty", ["All"] + sorted(list({c["difficulty"] for c in filtered_by_body}))
        )
        filtered_ch = filtered_by_body if sel_difficulty == "All" else [
            c for c in filtered_by_body if c["difficulty"] == sel_difficulty
        ]
        st.markdown("### Generate a Workout Program")
        num_exercises = min(5, len(filtered_ch))
        if st.button("Create My Workout Program"):
            if not filtered_ch:
                st.warning("No exercises found for this selection.")
            else:
                workout_program = random.sample(filtered_ch, num_exercises) if len(filtered_ch) >= num_exercises else filtered_ch
                st.session_state["workout_program"] = workout_program
        if "workout_program" in st.session_state:
            st.markdown("#### Your Workout Program:")
            for idx, ex in enumerate(st.session_state["workout_program"], 1):
                st.markdown(
                    f"**{idx}. {ex['title']}**\n\n{ex['description']}\n\n"
                    f"*Difficulty: {ex['difficulty']}; Equipment: {ex['equipment']}; Body Part: {ex.get('body_part', 'N/A')}*"
                )
            if st.button("Mark Program as Completed"):
                for ex in st.session_state["workout_program"]:
                    user.completed_challenges.add(ex["title"])
                today_str = datetime.now().strftime("%Y-%m-%d")
                user.viewed_calendar.add(today_str)
                st.success("Workout program completed!")
                save_current_user()
                del st.session_state["workout_program"]
        st.write(f"Challenges completed: {len(user.completed_challenges)}")

# --- Motivation/Calendar Tab (formerly Motivation) ---
with tab2:
    # --- Motivation Feature: auto-refresh quote every 20 seconds ---
    quotes = load_quotes_file()
    st.header("Daily Motivation")
    if quotes:
        # Use session_state to keep track of quote and timestamp
        if "quote_time" not in st.session_state or "quote_idx" not in st.session_state:
            st.session_state.quote_time = time.time()
            st.session_state.quote_idx = random.randint(0, len(quotes)-1)
        # Change quote every 20 seconds
        if time.time() - st.session_state.quote_time > 20:
            st.session_state.quote_time = time.time()
            st.session_state.quote_idx = random.randint(0, len(quotes)-1)
            st.rerun()
        quote = quotes[st.session_state.quote_idx]
        st.write(f'"{quote["text"]}" - *{quote["author"]}*')
        # Add a progress bar for user feedback
        st.progress(min(1, (time.time() - st.session_state.quote_time) / 20))
    else:
        st.info("No motivational quotes available.")

    # --- Calendar Section ---
    st.markdown("### 🗓️ Workout Calendar")
    today = datetime.now()
    year, month = today.year, today.month
    month_days = calendar.monthrange(year, month)[1]
    first_weekday = calendar.monthrange(year, month)[0]  # 0=Monday

    # Get set of completed days for this month
    completed_days = {int(date.split('-')[2]) for date in user.viewed_calendar if date.startswith(f"{year}-{month:02d}")}

    # Build calendar grid
    week_days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    cal = [["" for _ in range(7)] for _ in range(6)]
    day = 1
    for week in range(6):
        for wd in range(7):
            if (week == 0 and wd < first_weekday) or day > month_days:
                continue
            style = ""
            if day == today.day:
                style = "background-color:#ffe066; border-radius:8px;"  # Highlight today
            if day in completed_days:
                style = "background-color:#b6fcb6; border-radius:8px;"  # Green for completed
            cal[week][wd] = f"<div style='padding:6px;{style}'>{day}</div>"
            day += 1

    # Remove empty weeks
    cal = [row for row in cal if any(cell for cell in row)]

    # Display as HTML table
    table_html = "<table style='border-collapse:collapse;width:100%;text-align:center;'>"
    table_html += "<tr>" + "".join(f"<th>{wd}</th>" for wd in week_days) + "</tr>"
    for row in cal:
        table_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)

# --- Achievements Tab ---
with tab3:
    if role == "Coach":
        st.header("Client Achievements Overview")
        client_info, badge_names = get_client_achievements(badges)
        if not client_info:
            st.info("No client data to display.")
        else:
            st.dataframe(
                {
                    "Client": [c["username"] for c in client_info],
                    **{badge: ["✅" if badge in c["badges"] else "❌" for c in client_info] for badge in badge_names},
                },
                use_container_width=True,
            )
    else:
        st.header("Achievements")
        badge_names = set(b["name"] for b in badges)
        if len(user.completed_challenges) >= 10:
            user.earned_badges.add("10 Workouts")
        if "10 Workouts" in badge_names and "10 Workouts" in user.earned_badges:
            st.success("🏅 10 Workouts: Complete 10 unique challenges")
        if len(user.completed_challenges) >= 7:
            user.earned_badges.add("Streak Week")
        if "Streak Week" in badge_names and "Streak Week" in user.earned_badges:
            st.success("🏅 Streak Week: Complete challenges 7 days in a row")
        for badge in badges:
            if badge["name"] not in user.earned_badges:
                st.info(f"🔒 {badge['name']} (Locked)")
        st.write(f"Badges earned: {', '.join(user.earned_badges) if user.earned_badges else 'None yet.'}")
        save_current_user()

# --- Messages Tab ---
with tab4:
    st.header("Coach–Client Message Board")
    if role == "Coach":
        st.subheader("Post a Message for Your Clients")
        new_message = st.text_input("Write a message", key="new_message_input")
        new_category = st.selectbox("Category", ["General", "Urgent", "Info"], key="new_msg_cat")
        if st.button("Post Message", key="post_coach_msg_btn"):
            if new_message.strip():
                user.messages.append(Message(new_message.strip(), user.user_id, [new_category]))
                st.success("Message posted for clients!")
                save_current_user()
                st.rerun()
        st.subheader("Your Messages (Threads)")
        if user.messages:
            for idx, msg in enumerate(user.messages[::-1]):
                st.markdown(f"**{msg.content}** \n_{msg.timestamp}_ — {', '.join(msg.categories)}")
                if msg.replies:
                    st.markdown("**Replies:**")
                    for r_idx, reply in enumerate(msg.replies):
                        st.write(f"- {reply['content']} _(by {reply['author_id']} at {reply['timestamp']})_")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Delete Message #{idx+1}", key=f"del_msg_{idx}"):
                        real_idx = len(user.messages) - 1 - idx
                        user.messages.pop(real_idx)
                        st.success("Message deleted!")
                        save_current_user()
                        st.rerun()
                with col2:
                    reply_text = st.text_input(f"Reply to message #{idx+1}", key=f"coach_reply_{idx}")
                    if st.button(f"Post Reply #{idx+1}", key=f"post_reply_coach_{idx}"):
                        if reply_text.strip():
                            real_idx = len(user.messages) - 1 - idx
                            if not hasattr(user.messages[real_idx], "replies") or user.messages[real_idx].replies is None:
                                user.messages[real_idx].replies = []
                            user.messages[real_idx].replies.append(
                                {
                                    "content": reply_text.strip(),
                                    "author_id": user.username,
                                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                                }
                            )
                            st.success("Reply posted!")
                            save_current_user()
                            st.rerun()
        else:
            st.info("No messages posted yet.")
    else:
        all_users = load_users()
        coach_msgs = [
            (u["username"], m)
            for u in all_users.values() if u.get("role") == "Coach"
            for m in u.get("messages", [])
        ]
        coach_msgs = sorted(coach_msgs, key=lambda x: x[1]["timestamp"], reverse=True)
        if coach_msgs:
            for idx, (coach_name, msg) in enumerate(coach_msgs):
                st.markdown(
                    f"**From Coach {coach_name}:** \n> {msg['content']} \n_{msg['timestamp']}_ — {', '.join(msg.get('categories', []))}"
                )
                if msg.get("replies"):
                    st.markdown("**Replies:**")
                    for reply in msg["replies"]:
                        st.write(f"- {reply['content']} _(by {reply['author_id']} at {reply['timestamp']})_")
                with st.form(f"reply_form_{coach_name}_{idx}"):
                    reply_input = st.text_input("Your reply:", key=f"client_reply_input_{coach_name}_{idx}")
                    reply_submit = st.form_submit_button("Reply")
                    if reply_submit and reply_input.strip():
                        users_dict = load_users()
                        found = False
                        for coach_email, coach_data in users_dict.items():
                            if coach_data.get("username") == coach_name and coach_data.get("role") == "Coach":
                                for stored_msg in coach_data.get("messages", []):
                                    if (
                                        stored_msg["content"] == msg["content"]
                                        and stored_msg["timestamp"] == msg["timestamp"]
                                    ):
                                        if "replies" not in stored_msg or stored_msg["replies"] is None:
                                            stored_msg["replies"] = []
                                        stored_msg["replies"].append(
                                            {
                                                "content": reply_input.strip(),
                                                "author_id": user.username,
                                                "timestamp": datetime.now().isoformat(timespec="seconds"),
                                            }
                                        )
                                        save_users(users_dict)
                                        st.success("Reply posted!")
                                        st.rerun()
                                        found = True
                                        break
                            if found:
                                break
        else:
            st.info("No coach messages available yet.")

# --- Leaderboard Tab ---
with tab5:
    st.header("🏅 User Leaderboard")
    rankings = get_user_rankings()
    for idx, entry in enumerate(rankings, 1):
        st.write(f"{idx}. **{entry['username']}** — {entry['completed']} workouts completed")
    my_rank = next(
        (i + 1 for i, entry in enumerate(rankings) if entry["username"] == user.username), None
    )
    if my_rank:
        st.info(f"Your rank: {my_rank}")

with tab1:
    if role == "Coach":
        st.header("Create Workout Plan for Clients")
        challenges = load_challenges_file()
        workout_titles = [c["title"] for c in challenges]
        plan_name = st.text_input("Plan Name")
        selected_workouts = st.multiselect("Select Workouts for Plan", workout_titles)
        if st.button("Create Plan"):
            if not plan_name or not selected_workouts:
                st.warning("Please provide a plan name and select at least one workout.")
            else:
                # Save plan to a JSON file (one per plan, or all in one file)
                plans_file = "data/workout_plans.json"
                if os.path.exists(plans_file):
                    with open(plans_file, "r", encoding="utf-8") as f:
                        plans = json.load(f)
                else:
                    plans = {}
                plans[plan_name] = selected_workouts
                with open(plans_file, "w", encoding="utf-8") as f:
                    json.dump(plans, f, indent=2)
                st.success("Workout plan created!")
                st.header("Available Workout Plans for Clients")
                plans_file = "data/workout_plans.json"
                if os.path.exists(plans_file):
                    with open(plans_file, "r", encoding="utf-8") as f:
                        plans = json.load(f)
                    for pname, workouts in plans.items():
                        st.markdown(f"**{pname}**: {', '.join(workouts)}")
                else:
                    st.info("No workout plans created yet.")












