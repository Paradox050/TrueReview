from flask import request, redirect, jsonify, session, render_template, url_for, send_file
from controllers.sentiment_controller import analyze_product_reviews
from werkzeug.security import generate_password_hash, check_password_hash
from controllers.google_oauth import handle_google_authorize
from utils.pdf_utils import get_user_pdfs, get_pdf_by_id, delete_pdf_by_id
import io

def register_routes(app):
    # -------------------- HOME -------------------- #
    @app.route('/')
    def home():
        return render_template('home.html')

    # ------------------ LOGIN PAGE ------------------ #
    @app.route('/login', methods=['GET', 'POST'])
    def manual_login():
        if request.method == 'GET':
            return render_template('login.html')
        email = request.form.get('email')
        password = request.form.get('password')
        user = app.db.users.find_one({'email': email})
        if not user or not check_password_hash(user.get('password'), password):
            return "Invalid credentials", 401
        session['user'] = {'email': email, 'name': user.get('name')}
        return redirect('/')

    # ------------------ SIGNUP PAGE ------------------ #
    @app.route('/signup', methods=['GET', 'POST'])
    def manual_signup():
        if request.method == 'GET':
            return render_template('signup.html')
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        if app.db.users.find_one({'email': email}):
            return "User already exists", 400
        hashed_password = generate_password_hash(password)
        app.db.users.insert_one({
            'email': email,
            'password': hashed_password,
            'name': name
        })
        session['user'] = {'email': email, 'name': name}
        return redirect('/')

    # ------------------ GOOGLE OAUTH ------------------ #
    @app.route('/google-login')
    def google_login():
        return app.google.authorize_redirect(url_for('authorize', _external=True))

    @app.route('/google-signup')
    def google_signup():
        return app.google.authorize_redirect(url_for('authorize', _external=True))

    @app.route('/authorize')
    def authorize():
        return handle_google_authorize(app, app.google)

    # ------------------ LOGOUT ------------------ #
    @app.route('/logout')
    def logout():
        session.clear()
        return render_template('logout.html')

    # ------------------ PROFILE ------------------ #
    @app.route('/profile')
    def profile():
        if 'user' not in session:
            return redirect('/')
        return render_template('profile.html', user=session['user'])

    # ------------------ CHECK LOGIN ------------------ #
    @app.route('/check-login')
    def check_login():
        return jsonify({'loggedIn': 'user' in session})

    # ------------------ INDEX ------------------ #
    @app.route('/index')
    def index():
        if 'user' not in session:
            return redirect('/login-page')
        return render_template('index.html')

    # ------------------ ANALYZE (EXISTING) ------------------ #
    @app.route('/analyze_url', methods=['POST'])
    def analyze_url():
        product_url = request.form.get("product_url")
        if not product_url:
            return "No product URL provided", 400

        try:
            session['last_url'] = product_url
            analyze_product_reviews(product_url)
            return redirect('/dashboard/')
        except Exception as e:
            return f"Error during analysis: {str(e)}", 500

    @app.route('/analyze', methods=['POST'])
    def analyze_api():
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        try:
            session['last_url'] = url
            review_data = analyze_product_reviews(url)

            sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
            reviews = []

            for review in review_data:
                sentiment = review['sentiment'].lower()
                sentiments[sentiment] += 1
                reviews.append({
                    'text': review['text'],
                    'sentiment': sentiment
                })

            return jsonify({
                'logs': ['✅ Cookies loaded', '✅ Reviews scraped', '✅ Analysis complete'],
                'sentiments': sentiments,
                'reviews': reviews,
                'redirect_url': '/dashboard/'
            })

        except Exception as e:
            print('Error during analysis:', str(e))
            return jsonify({'error': 'Server error'}), 500

    # ------------------ GET USER SAVED PDFs ------------------ #
    @app.route('/get-user-pdfs')
    def get_user_pdf_list():
        if 'user' not in session:
            return jsonify({'pdfs': []})
        email = session['user']['email']
        pdfs = get_user_pdfs(app.db, email)
        return jsonify({
            'pdfs': [
                {'_id': str(pdf._id), 'filename': pdf.filename}
                for pdf in pdfs
            ]
        })

    # ------------------ DOWNLOAD SAVED PDF ------------------ #
    @app.route('/download-pdf/<pdf_id>')
    def download_pdf(pdf_id):
        try:
            pdf = get_pdf_by_id(app.db, pdf_id)
            return send_file(
                io.BytesIO(pdf.read()),
                download_name=pdf.filename,
                mimetype='application/pdf',
                as_attachment=True
            )
        except Exception as e:
            return f"❌ PDF not found or error: {str(e)}", 404

    # ------------------ DELETE SAVED PDF ------------------ #
    @app.route('/delete-pdf/<pdf_id>', methods=['POST'])
    def delete_pdf(pdf_id):
        try:
            delete_pdf_by_id(app.db, pdf_id)
            return jsonify({'status': 'deleted'})
        except Exception:
            return jsonify({'status': 'error'}), 500
