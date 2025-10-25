from openai import OpenAI
import streamlit as st

st.set_page_config(page_title="Streamlit Chat", page_icon="💬")
st.title("AI面接")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

if not st.session_state.setup_complete:

    st.subheader('個人情報', divider='rainbow')

    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    st.session_state["name"] = st.text_input(label="Name", value=st.session_state["name"], max_chars=40, placeholder="Enter your name")

    st.session_state["experience"] = st.text_area(label='経歴', value=st.session_state["experience"], height=None, max_chars=200, placeholder="あなたの経歴を入力してください。")

    st.session_state["skills"] = st.text_area(label="スキル", value=st.session_state["skills"], max_chars=200, placeholder="あなたのスキルを入力してください。")

    st.write(f"**お名前**:{st.session_state["name"]}")
    st.write(f"**経歴**: {st.session_state["experience"]}")
    st.write(f'**スキル**: {st.session_state["skills"]}')

    st.subheader("前職の会社名と、役職", divider='rainbow')

    if "level" not in st.session_state:
        st.session_state["level"] = "ジュニア"
    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"


    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
        "レベルを選択してください。",
        key = "visibility", 
        options = ["ジュニア", "ミドルレベル", "シニア"],
        )

    with col2:
        st.session_state["position"] = st.selectbox(
        "あなたの役職を選んでください",
        ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst")
        )

        st.session_state["company"] = st.selectbox(
        "希望する就職先",
        ("Amazon", "Meta", "Microsoft", "Apple", "NVIDIA", "Google", "Tesla", "野村證券株式会社")
    )

    st.write(f"**あなたの経歴**: {st.session_state["level"]}、{st.session_state["experience"]}、{st.session_state["skills"]}")

    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting interview...")

if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
    """
    これからあなたについての、質問も始めます。
    """
    )

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"

    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "system", 
            "content": f"You are an HR executive that interviews an interviewee called {st.session_state["name"]} with experience {st.session_state["experience"]} and skills {st.session_state["skills"]}. You should interview them for the position {st.session_state["level"]} {st.session_state["position"]} at the company {st.session_state["company"]}."}]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer", max_chars=1000):
            st.session_state.messages.append({"role":"user", "content":prompt}) 
            with st.chat_message("user"):
                st.markdown(prompt)
            
            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[{"role": m["role"], "content": m["content"]}
                                for m in st.session_state.messages
                                ],
                                stream=True,
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})

            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("フィードバックを受ける", on_click=show_feedback):
        st.write("Fetching feedback...")

if st.session_state.feedback_shown:
    st.subheader("フィードバック")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    feedback_completion = feedback_client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {"role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.
             Before the Feedback give a score of 1 to 10.
             Follow this format:
             Overal Score: //Your score
             Feedback: //Here you put your feedback
             Give only the feedback do not ask any additional questins.
             """},
            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any converstation: {conversation_history}"}
        ]
    )

    st.write(feedback_completion.choices[0].message.content)

    if st.button("Restart Interview", type="primary"):
        st.session_state.clear()
        st.experimental_rerun()
