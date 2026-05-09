# 🥗 Food Tracker (Flask + SQLite)

A local food & macro tracker with a dark-themed web UI.

## Project Structure

"""

food_tracker/ 
├── app.py                  # Flask backend (SQLite via sqlite3) 
├── food_tracker.db         # Auto-created SQLite database 
├── templates/ 
│   ├── base.html           # Shared layout (header, nav, toast) 
│   ├── home.html           # Date cards page 
│   ├── add_food.html       # Food library + add food page 
│   ├── view_date.html      # Daily food log page 
│   ├── login.htm        # User + admin login/register 
│   └── admin.html          #Admin dashboard 
├── static/ 
│   └── css/ 
│       └── style.css       # All shared styles 
└── food_tracker.bat       #Runs Windows terminal to download Python/Flask and runs the Food tracker website

"""


## How to Run
 
### Windows
Double-click `food_tracker.bat

### Manual (Wiindows or mac)

Install Python
```bash
pip install flask
cd "Folder loaction"
python app.py
```

Then open **http://localhost:5000** in your browser.


## API Endpoints

Method	Route	Description

Auth
GET	/login	    Login page	
POST	/api/auth/login	    Log in as user or admin	
POST	/api/auth/register	   Register a new user account	
POST	/api/auth/logout	End the current session	
GET	/api/auth/me	    Get current session info	

Foods
GET	/api/foods	    List all foods for current user
POST	/api/foods	    Create a new food item
PUT	/api/foods/:fid	    Update a food item
DELETE	/api/foods/:fid	    Delete a food item

Dates
GET	/api/dates	    List all date records with food IDs
POST	/api/dates	    Create a new date record
DELETE	/api/dates/:did	    Delete a date record
POST	/api/dates/:did/foods	    Add a food to a date
DELETE	/api/dates/:did/foods/:fid	    Remove a food from a date

Admin
GET	/api/admin/users	    List all registered users
DELETE	/api/admin/users/:uid	    Delete user and all their data
GET	/api/admin/users/:uid/dates	    Get a user's date records
GET	/api/admin/users/:uid/foods	    Get a user's food library

Pages
GET	/	    Home — date list dashboard	
GET	/add-food	    Add / manage food items	
GET	/view-date?id=:did	    View and log foods for a date	
GET	/admin		  Admin dashboard