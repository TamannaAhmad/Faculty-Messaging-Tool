import os
import pandas as pd
import streamlit as st
import pywhatkit as kit
from twilio.rest import Client

@st.cache_data
def send_whatsapp_image(image, students_info):
    data = pd.read_csv(students_info)
    for i in data.index:
        p_no = "+91" + str(data.loc[i, ['Parent Phone Number']].item())
        try: 
            kit.sendwhats_image(p_no, image, wait_time = 45, tab_close = True, close_time= 15)
        except Exception as e:
            print(f'Failed to send message to {p_no}. Error: {e}')
    return

@st.cache_data
def send_message(name, message, phone_no, service):
    if service == "WHATSAPP":
        try:
            #send message using PyWhatKit
            kit.sendwhatmsg_instantly(phone_no, message, wait_time=32, tab_close=True, close_time=15)
            return
        except Exception as e:
            print(f"Failed to send message to {name}. Error: {e}")
    elif service == "SMS":
        account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        auth_token = os.environ["TWILIO_AUTH_TOKEN"]
        from_number = os.environ["TWILIO_PHONE_NUMBER"]
        
        # validate environment variables
        if not all([account_sid, auth_token, from_number]):
            print("Missing Twilio credentials in environment variables.")
        client = Client(account_sid, auth_token)
        try:
            message = client.messages.create(
            body=message,
            from_=from_number,
            to=phone_no,
            )
            
        except Exception as e:
            print(f'Failed to send message to {name}. Error: {e}')
    else:
        print(f"Incorrect service {service} for student {name}.")
    return

@st.cache_data
def send_ia_marks(marks, students_info):
    #read the csv files into dataframes
    df_marks = pd.read_csv(marks) 
    df_students_info = pd.read_csv(students_info)

    #merge the dataframes using USN as key
    data = pd.merge(df_students_info, df_marks, on="USN")

    #get list of subjects
    subjects = data.columns[4:].tolist()

    #iterate through each student's data
    for i in df_marks.index: 
        #get each student's information
        name = data.loc[i, ['Student Name']].item()
        p_no = "+91" + str(data.loc[i, ['Parent Phone Number']].item())
        service = data.loc[i, ['Preferred Service']].item()
        student_marks = []
        #add marks of each subject to the list
        for j in subjects:
            student_marks.append(data.loc[i,j])

        message = f'Dear Parent, \nThis message is regarding the IA marks of your ward, {name}.\n'
        message += '\n'.join([f'{subject}: {marks}' for subject, marks in zip(subjects, student_marks)])
        message += '\nThank you.'

        send_message(name, message, p_no, service)
    return

@st.cache_data
def message_student(student_name, students_info, message):
    #read the csv files into dataframes
    df_students_info = pd.read_csv(students_info)
    p_no = p_no = "+91" + str(df_students_info.loc[df_students_info['Student Name'] == student_name, 'Parent Phone Number'].values[0])
    service = df_students_info.loc[df_students_info['Student Name'] == student_name, 'Preferred Service'].values[0]
    send_message(student_name, message, p_no, service)
    return 

def send_circular_ui():
    st.header("Send Circular")
    img = st.file_uploader('Upload Circular (jpg or png)')
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
    if students_file != None:
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
                    st.error(f"Error sending marks: {str(e)}")

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
                return
            except Exception as e:
                st.error(f"Error sending marks: {str(e)}")

st.set_page_config(
    page_title="Dashboard",
    page_icon="💻",
    layout="centered",
    initial_sidebar_state="expanded"
)

# initialize session state for host URL (needed for webhooks)
if 'host_url' not in st.session_state:
    st.session_state.host_url = "http://localhost:8501"

def main():
    st.title("Student Messaging Application")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a function:",
        ["Send I.A. Marks", "Circular", "Message a Parent"]
    )
    
    # Display the selected page
    if page == "Send I.A. Marks":
        send_ia_ui()
    elif page == "Circular":
        send_circular_ui()
        # summarizer_ui()
    elif page == "Message a Parent":
        send_message_ui()
    
    # Footer
    st.markdown("---")
    st.info(
        "This tool helps professors to easily send batch or single messages to their students."
    )

if __name__ == "__main__":
    main()
