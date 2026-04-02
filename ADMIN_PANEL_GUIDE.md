# Django Admin Panel Guide

## Backend Status
✅ **Backend is running** on `http://127.0.0.1:8000`
✅ **Admin Panel** available at `http://127.0.0.1:8000/admin/`

## Accessing the Admin Panel

1. **Start the server** (if not running):
   ```bash
   cd telemedicine_project
   .\venv\Scripts\Activate.ps1
   python manage.py runserver
   ```

2. **Create a superuser** (if you don't have one):
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to create an admin account.

3. **Access the admin panel**:
   - Open browser: `http://127.0.0.1:8000/admin/`
   - Login with your superuser credentials

## Available Models in Admin Panel

### 1. **Users** (`users.User`)
- **List Display**: Email, First Name, Last Name, Doctor Flag, Patient Flag, TMC Flag, Active Status
- **Filters**: Doctor, Patient, TMC Operator, Active, Staff, Superuser
- **Search**: Email, First Name, Last Name, Phone Number
- **Fieldsets**:
  - Email & Password
  - Personal Info (First Name, Last Name, Phone Number)
  - Roles (Doctor, Patient, TMC Operator)
  - Permissions (Active, Staff, Superuser, Groups, Permissions)

### 2. **Doctor Profiles** (`users.DoctorProfile`)
- **List Display**: 
  - User, Qualification, Specialty, License Number
  - Registration Number, Hospital/Clinic Name
  - Profile Completed Status, Active Status, Created At
- **Filters**: Profile Completed, Active, Specialty, Created At
- **Search**: User Email, First Name, Last Name, Qualification, Specialty, License Number, Registration Number, Hospital/Clinic Name
- **Fieldsets**:
  - **User Information**: User, Active Status, Profile Completed
  - **Professional Details**: Qualification, Specialty, Experience, License Number, Registration Number, Hospital/Clinic Name, Practice Type
  - **Specializations**: Major Diseases Specializations, Previous Hospitals Served
  - **Documents & Media**: Photo, Registration Certificate, Signature
  - **Settings**: Max Daily Consultations, Date of Birth
  - **Timestamps**: Created At, Updated At (collapsed)

### 3. **Patient Profiles** (`users.PatientProfile`)
- **List Display**: User, Gender, Age, Address, Active Status, Created At
- **Filters**: Gender, Active Status, Created At
- **Search**: User Email, First Name, Last Name, Gender, Address
- **Fieldsets**:
  - **User Information**: User, Active Status
  - **Personal Details**: Gender, Age, Address
  - **Timestamps**: Created At, Updated At (collapsed)

### 4. **TMC Profiles** (`users.TMCProfile`)
- **List Display**: 
  - User, Free Consultation Quota, Free Consultations Used
  - Free Consultations Remaining, Active Status, Created At
- **Filters**: Active Status, Created At
- **Search**: User Email, First Name, Last Name, TMC Details
- **Fieldsets**:
  - **User Information**: User, Active Status
  - **TMC Details**: TMC Details
  - **Free Consultation Quota**: Quota, Used, Remaining (read-only)
  - **Timestamps**: Created At, Updated At (collapsed)

### 5. **Doctor Availability** (`consultations.DoctorAvailability`)
- **List Display**: Doctor, Available Online, Available In-Clinic, Updated At
- **Search**: Doctor Email
- **Ordering**: Doctor Email

### 6. **Doctor Schedules** (`consultations.DoctorSchedule`)
- **List Display**: Doctor, Day of Week, Start Time, End Time, Online Status
- **Filters**: Day of Week, Online Status
- **Search**: Doctor Email, Day of Week
- **Ordering**: Doctor Email, Day of Week, Start Time

### 7. **Consultations** (`consultations.Consultation`)
- **List Display**: 
  - ID, Doctor, Patient, TMC, Consultation Type
  - Status, Free Status, Scheduled Time, Created At
- **Filters**: Status, Consultation Type, Free Status, Created At
- **Search**: Doctor Email, Patient Email, TMC Email
- **Ordering**: Created At (newest first)

### 8. **Consultation Records** (`consultations.ConsultationRecord`)
- **List Display**: Consultation, Video Recording, Created At
- **Search**: Doctor Email, Patient Email
- **Ordering**: Created At (newest first)

### 9. **Consultation Chats** (`consultations.ConsultationChat`)
- **List Display**: Consultation, Sender, Message, Timestamp, Read Status
- **Filters**: Read Status
- **Search**: Sender Email, Message
- **Ordering**: Timestamp (newest first)

### 10. **Prescriptions** (`consultations.Prescription`)
- **List Display**: Consultation, Doctor, Patient, Created At
- **Search**: Doctor Email, Patient Email, Medicines
- **Ordering**: Created At (newest first)

### 11. **Payments** (`consultations.Payment`)
- **List Display**: 
  - Consultation, Amount, Currency, Status
  - Paid by TMC, Created At
- **Filters**: Status, Paid by TMC, Currency
- **Search**: Consultation ID, Doctor Email, Patient Email
- **Ordering**: Created At (newest first)

## Features Available in Admin Panel

### ✅ View All Users
- See all registered users (doctors, patients, TMC operators)
- Filter by role, active status, staff status
- Search by email, name, or phone number

### ✅ View All Doctor Details
- Complete doctor profiles with all fields
- See profile completion status
- View qualifications, specialties, licenses
- Check registration certificates and photos
- Monitor daily consultation limits

### ✅ View All Patient Details
- Patient profiles with personal information
- Gender, age, and address details
- Active/inactive status

### ✅ View All TMC Details
- TMC operator profiles
- Free consultation quota management
- Track quota usage

### ✅ Manage Consultations
- View all consultation requests
- Filter by status, type, date
- See consultation history

### ✅ Monitor System Activity
- View all payments
- Check prescriptions
- Review chat messages
- Monitor doctor availability and schedules

## Quick Actions

### Create a Superuser
```bash
python manage.py createsuperuser
```

### Access Admin Panel
1. Navigate to: `http://127.0.0.1:8000/admin/`
2. Login with superuser credentials
3. Browse all models from the left sidebar

### Useful Admin Features
- **Bulk Actions**: Select multiple items and perform actions
- **Filters**: Use filters to narrow down results
- **Search**: Quick search across relevant fields
- **Export**: Export data (if django-import-export is installed)
- **Inline Editing**: Edit related objects inline

## Notes

- All models are properly registered and accessible
- Doctor profiles show all new fields including registration details
- Profile completion status is visible for doctors
- All consultation-related models are organized under the consultations app
- Timestamps are shown but collapsed by default for cleaner UI

