from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib import messages
from django.http import JsonResponse
from .models import User, Insurance
from .utils import extract_text_from_pdf, process_text_with_gemini, parse_insurance_data
from datetime import datetime
import json

# Create your views here.
class IndexView(TemplateView):
    template_name = "Webpages/index.html"

class LogoutView(View):
    def get(self, request):
        # Clear the session
        request.session.flush()
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')

class LoginPage(View):
    template_name = "Webpages/login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username, password=password)
            # Store user ID in session
            request.session['user_id'] = user.id
            return redirect('upload')
        except User.DoesNotExist:
            messages.error(request, 'Invalid username or password')
            return render(request, self.template_name)

class RegisterPage(View):
    template_name = "Webpages/register.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, self.template_name)

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, self.template_name)

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, self.template_name)

        user = User.objects.create(
            username=username,
            email=email,
            password=password
        )
        # Store user ID in session after registration
        request.session['user_id'] = user.id
        messages.success(request, 'Registration successful!')
        return redirect('upload')

class InsuranceListView(View):
    template_name = "Webpages/insurances.html"

    def get(self, request):
        # Check if user is logged in
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Please log in to view your insurance records')
            return redirect('login')
        
        # Get insurance records for the current user
        insurances = Insurance.objects.filter(user_id=user_id).order_by('-starting_date')
        return render(request, self.template_name, {'insurances': insurances})

    def post(self, request):
        # Check if user is logged in
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Please log in')
            return redirect('login')
            
        # Handle delete request
        if 'delete_id' in request.POST:
            try:
                insurance_id = request.POST.get('delete_id')
                # Only allow deletion of user's own records
                insurance = get_object_or_404(Insurance, id=insurance_id, user_id=user_id)
                insurance.delete()
                messages.success(request, 'Insurance record deleted successfully')
                return redirect('insurance_list')
            except Exception as e:
                messages.error(request, str(e))
                return redirect('insurance_list')
        return redirect('insurance_list')

class InsuranceDetailView(View):
    template_name = "Webpages/insurance_detail.html"

    def get(self, request, insurance_id):
        # Check if user is logged in
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Please log in to view insurance details')
            return redirect('login')
            
        # Only allow viewing of user's own records
        insurance = get_object_or_404(Insurance, id=insurance_id, user_id=user_id)
        return render(request, self.template_name, {'insurance': insurance})

class InsuranceEditView(View):
    template_name = "Webpages/insurance_edit.html"

    def get(self, request, insurance_id):
        # Check if user is logged in
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Please log in to edit insurance records')
            return redirect('login')
            
        # Only allow editing of user's own records
        insurance = get_object_or_404(Insurance, id=insurance_id, user_id=user_id)
        return render(request, self.template_name, {'insurance': insurance})

    def post(self, request, insurance_id):
        # Check if user is logged in
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Please log in to edit insurance records')
            return redirect('login')
            
        # Only allow editing of user's own records
        insurance = get_object_or_404(Insurance, id=insurance_id, user_id=user_id)
        try:
            insurance.car_brand = request.POST.get('car_brand')
            insurance.car_model = request.POST.get('car_model')
            insurance.VIN = request.POST.get('VIN')
            insurance.starting_date = datetime.strptime(request.POST.get('starting_date'), '%Y-%m-%d')
            insurance.expiry_date = datetime.strptime(request.POST.get('expiry_date'), '%Y-%m-%d')
            insurance.save()
            messages.success(request, 'Insurance record updated successfully')
            return redirect('insurance_list')
        except Exception as e:
            messages.error(request, f'Error updating insurance record: {str(e)}')
            return render(request, self.template_name, {'insurance': insurance})

class UploadView(View):
    template_name = "Webpages/upload.html"

    def get(self, request):
        # Check if user is logged in
        if not request.session.get('user_id'):
            messages.error(request, 'Please log in to upload insurance documents')
            return redirect('login')
        return render(request, self.template_name)

    def post(self, request):
        # Check if user is logged in
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Please log in to upload insurance documents')
            return redirect('login')
            
        try:
            # Get the uploaded file
            insurance_file = request.FILES.get('insurance_file')
            
            if not insurance_file:
                messages.error(request, 'No file uploaded')
                return render(request, self.template_name)
            
            # Check if file is PDF
            if not insurance_file.name.endswith('.pdf'):
                messages.error(request, 'Please upload a PDF file')
                return render(request, self.template_name)
            
            # Extract text from PDF
            extracted_text = extract_text_from_pdf(insurance_file)
            if not extracted_text:
                messages.error(request, 'Error extracting text from PDF')
                return render(request, self.template_name)
            
            # Process text with Gemini
            gemini_response = process_text_with_gemini(extracted_text)
            if not gemini_response:
                messages.error(request, 'Error processing document with AI')
                return render(request, self.template_name)
            
            # Parse the insurance data
            insurance_data = parse_insurance_data(gemini_response)
            if not insurance_data:
                messages.error(request, 'Error parsing insurance data')
                return render(request, self.template_name)
            
            # Validate required fields
            required_fields = ['insurance_id', 'expiry_date', 'starting_date', 'car_brand', 'car_model', 'VIN']
            missing_fields = [field for field in required_fields if not insurance_data.get(field)]
            
            if missing_fields:
                messages.error(request, f'Missing required fields: {", ".join(missing_fields)}')
                return render(request, self.template_name)
            
            try:
                # Check if insurance record already exists for this user
                existing_insurance = Insurance.objects.filter(
                    user_id=user_id,
                    insurance_id=insurance_data['insurance_id']
                ).first()
                
                if existing_insurance:
                    messages.error(request, f'An insurance record with ID {insurance_data["insurance_id"]} already exists in your database. Please upload a different file or use the manual entry form to update the existing record.')
                    return render(request, self.template_name)
                
                # Create new insurance record
                insurance = Insurance.objects.create(
                    user_id=user_id,  # Associate with current user
                    insurance_id=insurance_data['insurance_id'],
                    expiry_date=datetime.strptime(insurance_data['expiry_date'], '%Y-%m-%d'),
                    starting_date=datetime.strptime(insurance_data['starting_date'], '%Y-%m-%d'),
                    car_brand=insurance_data['car_brand'],
                    car_model=insurance_data['car_model'],
                    VIN=insurance_data['VIN']
                )
                
                messages.success(request, 'Insurance document processed successfully!')
                return redirect('insurance_list')
                
            except ValueError as e:
                messages.error(request, f'Invalid date format: {str(e)}')
                return render(request, self.template_name)
            except Exception as e:
                messages.error(request, f'Error saving insurance data: {str(e)}')
                return render(request, self.template_name)
            
        except Exception as e:
            messages.error(request, f'Error processing document: {str(e)}')
            return render(request, self.template_name)

class InsuranceFormView(View):
    def get(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        # Get all insurance records for the current user to populate the dropdown
        insurances = Insurance.objects.filter(user_id=user_id).order_by('-starting_date')
        return render(request, 'Webpages/insurance_form.html', {'insurances': insurances})
    
    def post(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        # Get form data
        car_brand = request.POST.get('car_brand')
        car_model = request.POST.get('car_model')
        VIN = request.POST.get('VIN')
        starting_date = request.POST.get('starting_date')
        expiry_date = request.POST.get('expiry_date')
        insurance_id = request.POST.get('insurance_id')
        
        # Validate required fields
        if not all([car_brand, car_model, VIN, starting_date, expiry_date, insurance_id]):
            messages.error(request, 'All fields are required.')
            return redirect('insurance_form')
        
        # Check if insurance_id already exists for this user
        if Insurance.objects.filter(user_id=user_id, insurance_id=insurance_id).exists():
            messages.error(request, 'Insurance ID already exists for your account.')
            return redirect('insurance_form')
        
        try:
            # Create new insurance record
            insurance = Insurance.objects.create(
                user_id=user_id,
                car_brand=car_brand,
                car_model=car_model,
                VIN=VIN,
                starting_date=starting_date,
                expiry_date=expiry_date,
                insurance_id=insurance_id
            )
            messages.success(request, 'Insurance record created successfully.')
            return redirect('insurance_list')
        except Exception as e:
            messages.error(request, f'Error creating insurance record: {str(e)}')
            return redirect('insurance_form')