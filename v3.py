import os
import requests
import pandas as pd
import streamlit as st

WASSENGER_API_KEY = os.environ["WASSENGER_API"]
WASSENGER_MSG_URL = "https://api.wassenger.com/v1/messages"
WASSENGER_FILE_URL = "https://api.wassenger.com/v1/files"

HEADERS = {
    "Content-Type": "application/json",
    "Token": WASSENGER_API_KEY
}

# Helper: Send WhatsApp text message via Wassenger
@st.cache_data
def send_whatsapp_message(phone, message):
    payload = {
        "phone": phone,
        "message": message
    }
    try:
        response = requests.post(WASSENGER_MSG_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to send message to {phone}. Error: {e}")
        return None

# Helper: Upload image to Wassenger and return file id
@st.cache_data
def upload_image_to_wassenger(image_file):
    headers = {"Token": WASSENGER_API_KEY}
    files = {"file": (image_file.name, image_file, image_file.type)}
    try:
        response = requests.post(WASSENGER_FILE_URL, headers=headers, files=files)
        response.raise_for_status()
        file_id = response.json()[0]["id"]
        return file_id
    except Exception as e:
        print(f"Failed to upload image. Error: {e}")
        return None

# Helper: Send WhatsApp image message via Wassenger
@st.cache_data
def send_whatsapp_image_message(phone, message, file_id):
    payload = {
        "phone": phone,
        "message": message,
        "media": {"file": file_id}
    }
    try:
        response = requests.post(WASSENGER_MSG_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to send image to {phone}. Error: {e}")
        return None

# Send circular image to all parents in students_info
@st.cache_data
def send_whatsapp_image(image, students_info):
    data = pd.read_csv(students_info)
    file_id = upload_image_to_wassenger(image)
    if not file_id:
        print("Image upload failed. Aborting.")
        return
    for i in data.index:
        p_no = "+91" + str(data.loc[i, ['Phone Number']].item())
        send_whatsapp_image_message(p_no, "Please find the attached circular.", file_id)
    return

# Send a text message to a parent
@st.cache_data
def send_message(name, message, phone_no):
    send_whatsapp_message(phone_no, message)
    return

# Send IA marks to all parents
@st.cache_data
def send_ia_marks(marks, students_info):
    df_marks = pd.read_csv(marks)
    df_students_info = pd.read_csv(students_info)
    data = pd.merge(df_students_info, df_marks, on="USN")
    subjects = data.columns[3:].tolist()
    for i in df_marks.index:
        name = data.loc[i, ['Student Name']].item()
        p_no = "+91" + str(data.loc[i, ['Phone Number']].item())
        student_marks = [data.loc[i, j] for j in subjects]
        message = f'Dear Parent, \nThis message is regarding the IA marks of your ward, {name}.\n'
        message += '\n'.join([f'{subject}: {marks}' for subject, marks in zip(subjects, student_marks)])
        message += '\nThank you.'
        send_whatsapp_message(p_no, message)
    return

# Send a custom message to a specific student
@st.cache_data
def message_student(student_name, students_info, message):
    df_students_info = pd.read_csv(students_info)
    try:
        p_no = "+91" + str(df_students_info.loc[df_students_info['Student Name'] == student_name, 'Phone Number'].values[0])
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return
    send_whatsapp_message(p_no, message)
    return

def send_circular_ui():
    st.header("Send Circular")
    img = st.file_uploader('Upload Circular (jpg or png)', type=['jpg', 'jpeg', 'png'])
    semester = st.selectbox('Odd or Even Semester?', ['Odd', 'Even'])
    if semester == "Odd":
        semester_no = st.selectbox('Select Semester: ', [1, 3, 5, 7 ])
    else:
        semester_no = st.selectbox('Select Semester: ', [2, 4, 6, 8])
    students_file = st.file_uploader(f"Select the File for Semester {semester_no} Students")
    if st.button(f'Send Circular to Semester {semester_no} Parents'):
        with st.spinner('Sending Circular to Parents...'):
            try:
                send_whatsapp_image(img, students_file)
                st.success(f"Successfully Sent Circular to Parents for Semester {semester_no}")
            except Exception as e:
                st.error(f"Error Sending Circular: {str(e)}")

def send_message_ui():
    st.header("Message a Parent")
    students_file = st.file_uploader("Select the File for Students' Information: ")
    if students_file is not None:
        students_data = pd.read_csv(students_file)
        students_list = students_data['Student Name'].values.tolist()
        student_name = st.selectbox("Enter Student's Name:", students_list)
        message = st.text_input("Enter the Message to be Sent:")
        students_file.seek(0)
        if st.button(f"Send Message to {student_name}'s parents"):
            with st.spinner('Sending message to parents...'):
                try:
                    message_student(student_name, students_file, message)
                    st.success(f"Successfully sent message to {student_name}'s parents.")
                except Exception as e:
                    st.error(f"Error sending message: {str(e)}")

def send_ia_ui():
    st.header("Send I.A. Marks")
    semester = st.selectbox('Odd or Even Semester?', ['Odd', 'Even'])
    if semester == "Odd":
        semester_no = st.selectbox('Select a Semester: ', [1, 3, 5, 7 ])
    else:
        semester_no = st.selectbox('Select a Semester: ', [2, 4, 6, 8])
    ia = st.selectbox("Select the I.A.:", ['I.A. 1', 'I.A. 2', 'I.A. 3'])
    students_file = st.file_uploader("Select File for Students' Information:")
    marks_file = st.file_uploader(f"Select File for {ia} Marks:")    
    if st.button('Send IA Marks to Parents'):
        with st.spinner('Sending marks to parents...'):
            try:
                send_ia_marks(marks_file, students_file)
                st.success(f"Successfully sent {ia} marks to parents for Semester {semester_no}")
            except Exception as e:
                st.error(f"Error sending marks: {str(e)}")

st.set_page_config(
    page_title="Faculty Messaging Tool",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="expanded"
)

if 'host_url' not in st.session_state:
    st.session_state.host_url = "http://localhost:8501"

def main():
    st.title("Student Messaging Application")
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a function:",
        ["Send I.A. Marks", "Circular", "Message a Parent"]
    )
    if page == "Send I.A. Marks":
        send_ia_ui()
    elif page == "Circular":
        send_circular_ui()
    elif page == "Message a Parent":
        send_message_ui()
    st.markdown("---")
    st.info(
        "This tool helps professors to easily send batch or single messages to their students."
    )

if __name__ == "__main__":
    main() 