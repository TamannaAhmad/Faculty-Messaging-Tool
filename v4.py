import os
import requests
import pandas as pd
import streamlit as st
from pathlib import Path

# API ENVIRONMENT VARIABLES & URLS 

WASSENGER_API_KEY = os.environ["WASSENGER_API"]
WASSENGER_MSG_URL = "https://api.wassenger.com/v1/messages"
WASSENGER_FILE_URL = "https://api.wassenger.com/v1/files"

HEADERS = {
    "Content-Type": "application/json",
    "Token": WASSENGER_API_KEY
}

# MAIN API CALL 
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
        st.error(f"Failed to send message to {phone}. Error: {e}")
        return None
    
# UPLOAD IMAGE TO WASSENGER, RETURN FILE ID
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

# API CALL TO SEND MESSAGE WITH IMAGE
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

# FUNCTION TO SEND IA MARKS TO PARENTS
@st.cache_data
def send_ia_marks(students_info, marks, ia):
    df_students_info = pd.read_excel(students_info)
    df_marks = pd.read_excel(marks, sheet_name = 'IA ' + str(ia))
    
    data = pd.merge(df_students_info, df_marks, on="USN")
    subjects = data.columns[3:].tolist() # this is assuming the user has followed the excel format instructions
    for i in df_marks.index:
        # reading individual's information from the file
        name = data.loc[i, ['Student Name']].item()
        p_no = "+91" + str(data.loc[i, ['Phone Number']].item())
        student_marks = [data.loc[i, j] for j in subjects]

        # message template for IA marks
        message = f'Dear Parent, \nThis message is regarding the I.A. {ia} marks of your ward, {name}.\n'
        message += '\n'.join([f'{subject}: {marks}' for subject, marks in zip(subjects, student_marks)])
        message += '\nThank you.'

        response = send_whatsapp_message(p_no, message)
    return response

# FUNCTION TO SEND CIRCULAR TO PARENTS
@st.cache_data
def send_whatsapp_image(students_info, image):
    data = pd.read_excel(students_info, )
    file_id = upload_image_to_wassenger(image)

    if not file_id:
        print("Image upload failed. Aborting.")
        return
    
    for i in data.index:
        p_no = "+91" + str(data.loc[i, ['Phone Number']].item())
        send_whatsapp_image_message(p_no, "Please find the attached circular.", file_id)
    return

# FUNCTION TO SEND MESSAGE TO SINGLE PARENT
@st.cache_data
def message_student(students_info, message, semester_no, student_usn = None, student_name = None):
    df_students_info = pd.read_excel(students_info, sheet_name='sem ' + str(semester_no))
    try:
        if (student_name):
            p_no = "+91" + str(df_students_info.loc[df_students_info['Student Name'] == student_name, 'Phone Number'].values[0])
            st.info(p_no)
        elif (student_usn):
            p_no = "+91" + str(df_students_info.loc[df_students_info['USN'] == student_usn, 'Phone Number'].values[0])
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return
    send_whatsapp_message(p_no, message)
    return

# STREAMLIT UI: SEND IA MARKS
def send_ia_ui():
    st.header("Send I.A. Marks")

    semester = st.selectbox('Odd or Even Semester?', ['Odd', 'Even'])
    if semester == "Odd":
        semester_no = st.selectbox('Select a Semester: ', [1, 3, 5, 7 ])
    else:
        semester_no = st.selectbox('Select a Semester: ', [2, 4, 6, 8])
    ia_num = st.selectbox("Select the I.A.:", ['I.A. 1', 'I.A. 2', 'I.A. 3'])

    option = st.selectbox('Upload or auto load files?', ['Auto Load', 'Upload'])

    if (option == 'Upload'):
        students_file = st.file_uploader(f"Upload File for {semester_no} Semester Students' Information:")
        marks_file = st.file_uploader(f"Upload File for {semester_no} Semester's IA  Marks:")    
    else:
        pathlist = Path().rglob('*.xlsx')
        string_paths = []
        for path in pathlist:
            # convert path from object to string
            path_in_str = str(path)
            string_paths.append(path_in_str)
        students_file = st.selectbox(f"Select File for {semester_no} Semester Students' Information:", string_paths)
        marks_file = st.selectbox(f"Select File for {semester_no} Semester's IA Marks:", string_paths)

    for i in range(len(ia_num)):
        if ia_num[i].isnumeric():
            ia = int(ia_num[i])
    
    if st.button('Send IA Marks to Parents'):
        with st.spinner('Sending marks to parents...'):
            try:    
                response = send_ia_marks(students_file, marks_file, ia)
            except Exception as e:
                st.error(f"Error sending marks: {str(e)}")
                return
        if response:
            st.success(f"Successfully sent I.A. {ia} marks to parents for Semester {semester_no}")
        else:
            return

# STREAMLIT UI: SEND CIRCULAR
def send_circular_ui():
    st.header("Send Circular")

    img = st.file_uploader('Upload Circular (jpg, jpeg, or png)', type=['jpg', 'jpeg', 'png'])
    semester = st.selectbox('Odd or Even Semester?', ['Odd', 'Even'])
    if semester == "Odd":
        semester_no = st.selectbox('Select Semester: ', [1, 3, 5, 7 ])
    else:
        semester_no = st.selectbox('Select Semester: ', [2, 4, 6, 8])

    option = st.selectbox('Upload or auto load files?', ['Auto Load', 'Upload'])

    if (option == 'Upload'):
        students_file = st.file_uploader(f"Upload File for {semester_no} Semester Students' Information:")
    else:
        pathlist = Path().rglob('*.xlsx')
        stringpath = []
        for path in pathlist:
            # convert path from object to string and append in list
            path_in_str = str(path)
            stringpath.append(path_in_str)
            
        students_file = st.selectbox(f"Select File for {semester_no} Semester Students' Information:", stringpath, index = None)
    

    if st.button(f'Send Circular to Semester {semester_no} Parents'):
        with st.spinner('Sending Circular to Parents...'):
            try:
                send_whatsapp_image(students_file, img)
            except Exception as e:
                st.error(f"Error Sending Circular: {str(e)}")
                return
        st.success(f"Successfully Sent Circular to Parents for Semester {semester_no}")
        return

# STREAMLIT UI: SEND SINGLE MESSAGE
def send_message_ui():
    st.header("Message a Parent")

    semester = st.selectbox('Odd or Even Semester?', ['Odd', 'Even'])
    if semester == "Odd":
        semester_no = st.selectbox('Select a Semester: ', [1, 3, 5, 7 ])
    else:
        semester_no = st.selectbox('Select a Semester: ', [2, 4, 6, 8])

    option = st.selectbox('Upload or auto load files?', ['Auto Load', 'Upload'])

    if (option == 'Upload'):
        students_file = st.file_uploader(f"Upload File for {semester_no} Semester Students' Information:")
    else:
        pathlist = Path().rglob('*.xlsx')
        string_paths = []
        for path in pathlist:
            # convert path from object to string
            path_in_str = str(path)
            string_paths.append(path_in_str)
        students_file = st.selectbox(f"Select File for {semester_no} Semester Students' Information:", string_paths, index = None)

    if students_file is not None:
        students_data = pd.read_excel(students_file, sheet_name= 'sem ' + str(semester_no))

        option = st.selectbox('Find Student by USN or Name?', ['USN', 'Name'])
        student_USN = None
        try:
            if option == "USN":
                USN_list = students_data['USN'].values.tolist()
                student_USN = st.selectbox("Select Student's USN: ", USN_list)
                student_name = students_data.loc[students_data['USN'] == student_USN, 'Student Name'].values[0]
            else: 
                names_list = students_data['Student Name'].values.tolist()
                student_name = st.selectbox("Select Student's Name:", names_list)
            message = st.text_input("Enter the Message to be Sent:")
            if st.button(f"Send Message to {student_name}'s parents"):
                with st.spinner('Sending message to parents...'):
                    try:
                        if (student_USN) :
                            message_student(students_file, message, semester_no, student_USN)
                        else: 
                            message_student(students_file, message, semester_no, student_name)
                    except Exception as e:
                        st.error(f"Error sending message: {str(e)}")
                        return
                st.success(f"Successfully sent message to {student_name}'s parents.")
                return
        except Exception as e:
            st.error(f"Error in selected file: {e}")
            st.info("Possible issues: the selected file does not contain student information, or is in a different format.")
            return
    else:
        st.error("Please Select a File")

# STREAMLIT MAIN FUNCTION

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