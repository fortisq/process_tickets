import requests
import datetime
import json
import time

# Replace with your SyncroMSP API key and subdomain
API_KEY = 'your_api_key'
SUBDOMAIN = 'your_subdomain'

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "accept": "application/json",
    "Content-Type": "application/json"
}

# Function to handle API responses and errors
def handle_response(response):
    try:
        response_data = response.json()
        if response.status_code in [200, 201]:
            return response_data
        else:
            print(f"Error {response.status_code}: {response_data}")
            return None
    except ValueError:
        print("Response is not valid JSON")
        print(response.text)
        return None

# Function to retrieve tickets with pagination
def get_all_tickets(created_after, created_before):
    page = 1
    all_tickets = []
    while True:
        response = requests.get(f'https://{SUBDOMAIN}.syncromsp.com/api/v1/tickets?created_after={created_after}&created_before={created_before}&mine=false&page={page}', headers=headers)
        tickets_data = handle_response(response)
        if tickets_data:
            tickets = tickets_data.get('tickets', [])
            if not tickets:
                break
            all_tickets.extend(tickets)
            page += 1
        else:
            break
    return all_tickets

# Function to add a time entry to a ticket
def add_time_entry(ticket_id):
    current_time = datetime.datetime.utcnow()
    start_time = current_time.isoformat() + "Z"
    end_time = (current_time + datetime.timedelta(hours=1)).isoformat() + "Z"
    time_entry_data = {
        "start_at": start_time,
        "end_at": end_time,
        "duration_minutes": 60,
        "user_id": 0,  # Adjust the user_id if necessary
        "notes": "Adding 1 hour of work.",
        "product_id": 0  # Adjust the product_id if necessary
    }
    response = requests.post(f'https://{SUBDOMAIN}.syncromsp.com/api/v1/tickets/{ticket_id}/timer_entry', headers=headers, json=time_entry_data)
    return handle_response(response)

# Function to update the status of a ticket to 'Resolved'
def update_ticket_status(ticket_id):
    update_data = {
        "status": "Resolved"
    }
    response = requests.put(f'https://{SUBDOMAIN}.syncromsp.com/api/v1/tickets/{ticket_id}', headers=headers, json=update_data)
    return handle_response(response)

# Main function to process tickets in 5-day intervals
def process_tickets():
    days_back = 0
    while True:
        created_after = (datetime.datetime.utcnow() - datetime.timedelta(days=days_back + 5)).strftime('%Y-%m-%d')
        created_before = (datetime.datetime.utcnow() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
        print(f"Processing tickets created between {created_after} and {created_before}")

        # Retrieve all tickets created within the specified 5-day period
        all_tickets = get_all_tickets(created_after, created_before)

        # Filter tickets to include only those with status 'New' or 'In Progress'
        filtered_tickets = [ticket for ticket in all_tickets if ticket['status'] in ['New', 'In Progress']]

        if not filtered_tickets:
            print("No more tickets to process.")
            break

        # Add a time entry and update the status for each filtered ticket
        for ticket in filtered_tickets:
            ticket_id = ticket['id']
            time_entry_result = add_time_entry(ticket_id)
            if time_entry_result:
                print(f"Time entry added for ticket {ticket_id}")
                status_update_result = update_ticket_status(ticket_id)
                if status_update_result:
                    print(f"Ticket {ticket_id} status updated to 'Resolved'")
                else:
                    print(f"Failed to update status for ticket {ticket_id}")
            else:
                print(f"Failed to add time entry for ticket {ticket_id}")
            # Add a delay to avoid hitting the rate limit
            time.sleep(0.5)  # Adjust the sleep time as needed

        days_back += 5

# Run the main function
process_tickets()
