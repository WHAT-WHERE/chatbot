from flask import Flask, render_template, request, jsonify, session
import datetime
from googletrans import Translator
from pytz import timezone

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Initialize the translator
translator = Translator()

# Function to save ticket details to a file
def save_ticket_info(ticket_count, ticket_time, ticket_amount):
    with open("file.txt", "a") as file:
        file.write(f"Ticket Count: {ticket_count}\n")
        file.write(f"Booking Time: {ticket_time}\n")
        file.write(f"Ticket Amount: {ticket_amount}\n")
        file.write("-" * 20 + "\n")

# Route for the homepage, displaying the language selection prompt
@app.route("/")
def index():
    session['step'] = 1  # Start at step 1
    session['language'] = 'en'  # Default language is English
    return render_template("index.html", message="Welcome! Please select your language (e.g., 'en' for English, 'hi' for Hindi):")

# Function to handle chatbot flow based on steps
def process_chatbot_flow(user_input, lang='en'):
    step = session.get('step', 1)  # Default to step 1 if not set
    response = ""
    
    # Step 1: Language selection
    if step == 1:
        session['language'] = user_input  # Set the language
        session['step'] = 2  # Move to next step
        age_prompt = "Are you above 18? Type '1' for Yes & '2' for No."
        response = f"Chatbot: {translator.translate(age_prompt, src='en', dest=session['language']).text}"
    
    # Step 2: Age confirmation
    elif step == 2:
        if '1' in user_input:  # User is above 18
            session['age_confirmed'] = True
            session['ticket_price'] = 200  # Adult price
        elif '2' in user_input:  # User is below 18
            session['age_confirmed'] = True
            session['ticket_price'] = 100  # Child price
        else:
            response = f"Chatbot: {translator.translate('Invalid input. Please type \'1\' for Yes and \'2\' for No.', src='en', dest=session['language']).text}"
            return response

        session['step'] = 3  # Move to next step
        ticket_prompt = f"The price is {session['ticket_price']} per ticket. How many tickets would you like to buy?"
        response = f"Chatbot: {translator.translate(ticket_prompt, src='en', dest=session['language']).text}"
    
    # Step 3: Number of tickets
    elif step == 3:
        try:
            ticket_count = int(user_input)
            session['ticket_count'] = ticket_count
            total_price = session['ticket_price'] * ticket_count
            session['step'] = 4  # Move to next step
            total_price_message = f"The total price for {ticket_count} tickets is {total_price}. Please select a payment method (e.g., UPI, card)."
            response = f"Chatbot: {translator.translate(total_price_message, src='en', dest=session['language']).text}"
        except ValueError:
            response = f"Chatbot: {translator.translate('Please enter a valid number of tickets.', src='en', dest=session['language']).text}"
    
    # Step 4: Payment method
    elif step == 4:
        payment_method = user_input.lower()
        session['payment_method'] = payment_method
        session['step'] = 5  # Move to final step
        
        payment_confirmation = f"You selected {payment_method} method.\nPayment is being processed...\nPayment completed!"
        response = f"Chatbot: {translator.translate(payment_confirmation, src='en', dest=session['language']).text}"
        
        # Adding a space before ticket details for clarity
        response += "\n\nChatbot: " + translator.translate("Here are your ticket details:", src='en', dest=session['language']).text + "\n"
        ticket_details = f"Number of tickets: {session.get('ticket_count')}\n"
        ticket_details += f"Total price: {session['ticket_price'] * session.get('ticket_count')}\n"
        ticket_details += f"Booking time: {datetime.datetime.now(timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')}"
        save_ticket_info(session.get('ticket_count'), datetime.datetime.now(), session['ticket_price'] * session.get('ticket_count'))
        
        response += translator.translate(ticket_details, src='en', dest=session['language']).text

        # Add a prompt for feedback after displaying ticket details
        feedback_prompt = "Would you like to provide feedback? Type 'yes' to continue or 'no' to exit."
        response += "\n\nChatbot: " + translator.translate(feedback_prompt, src='en', dest=session['language']).text
        session['step'] = 6  # Move to feedback step
    elif step == 6:
        if 'yes' in user_input.lower():
            session['step'] = 7
            response = f"Chatbot: {translator.translate('Please enter your feedback:', src='en', dest=session['language']).text}"
        elif 'no' in user_input.lower():
            response = f"Chatbot: {translator.translate('Thank you for using the ticket booking service!', src='en', dest=session['language']).text}"
            session.clear()  # Clear session to restart
        else:
            response = f"Chatbot: {translator.translate('Invalid input. Type \'yes\' to provide feedback or \'no\' to exit.', src='en', dest=session['language']).text}"
    
    elif step == 7:
        # Save feedback
        sendFeedback(session.get('ticket_count'), user_input)  # Call your feedback save function
        response = f"Chatbot: {translator.translate('Thank you for your feedback!', src='en', dest=session['language']).text}"
        session.clear()  # Clear session to restart

    return response



# Route for handling the chat interaction
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message").lower()
    session_language = session.get('language', 'en')  # Use the selected session language

    # Handle the chatbot flow
    response = process_chatbot_flow(user_input, session_language)

    return jsonify({"reply": response})

# Route for handling user feedback on the chatbot interaction
@app.route("/feedback", methods=["POST"])
def feedback():
    try:
        user_input = request.json.get("user_input")
        feedback = request.json.get("feedback")
        if not user_input or not feedback:
            return jsonify({"reply": "Invalid feedback input"}), 400  # Error if missing data

        # Attempt to write to file
        with open("feedback.txt", "a") as file:
            file.write(f"USER INPUT: {user_input}\n")
            file.write(f"FEEDBACK: {feedback}\n")
            file.write("-" * 20 + "\n")
        
        return jsonify({"reply": "Thank you for your feedback!"})
    
    except Exception as e:
        print(f"Error in feedback route: {e}")
        return jsonify({"reply": "Error handling feedback"}), 500

if __name__ == "__main__":
    app.run(debug=True)

