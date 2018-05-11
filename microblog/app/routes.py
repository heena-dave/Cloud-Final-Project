import os
import profilepictures
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, send_from_directory
from flask import jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from flask_babel import _, get_locale
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, \
    ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Post
from app.email import send_password_reset_email, send_email
from app.translate import translate
from guess_language import guess_language
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'profilepictures/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
	form = PostForm()
	if form.validate_on_submit():
		language = guess_language(form.post.data)
		if language == 'UNKNOWN' or len(language) > 5:
			language = ''
		post = Post(body=form.post.data, author=current_user,language=language)
		db.session.add(post)
		db.session.commit()
		flash(_('Your post is now live!'))
		return redirect(url_for('index'))
	page = request.args.get('page', 1, type=int)
	posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
	prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
	return render_template('index.html', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url,user=current_user)


@app.route('/explore')
@login_required
def explore():
	page = request.args.get('page', 1, type=int)
	posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
	prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
	return render_template('index.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url,user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title=_('Sign In'), form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('login'))
    return render_template('register.html', title=_('Register'), form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title=_('Reset Password'), form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('user', username=username))

@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})
									  
@app.route('/uploadpicture', methods=['GET','POST'])
@login_required
def upload_picture():
	message = ""
	username = current_user.username
	display = request.form['profilepic']
		
	if display == "Avatar":
		message = "Avatar is selected. File is not uploaded."
		object = User.query.filter_by(username=current_user.username).first()
		object.displayProfilePicture = False
		filename = secure_filename(current_user.username) + ".png"
		os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		db.session.commit()
		flash(message)
		return user(current_user.username)
	
	if 'photo' not in request.files:
		message = "No file selected to upload"
		flash(message)
		return user(current_user.username)
	
	file = request.files['photo']
    # if user does not select file, browser also
    # submit a empty part without filename
	if file.filename == '':
		message = "No file selected to upload"
		flash(message)
		return user(current_user.username)
		
	if file and allowed_file(file.filename) and display=="ProfilePic":
		filename = secure_filename(current_user.username) + ".png"
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		object = User.query.filter_by(username=current_user.username).first()
		object.displayProfilePicture = True
		db.session.commit()
		message = "File uploaded successfully"
		flash(message)
		return user(current_user.username)
	elif not allowed_file(file.filename):
		message = "Invalid file type."
		flash(message)
		return user(current_user.username)
		
	return user(current_user.username)
	
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
		   
@app.route('/profilepictures/<path>')
@login_required
def profilepictures(path):
	return send_from_directory("../profilepictures/",path)
	
@app.route('/<filename>')
@login_required
def loadimage(filename):
	return send_from_directory("../static/",filename)
	
@app.route('/sendemail/<post>')
@login_required
def sendemail(post):
	userPost = Post.query.filter_by(id=post).first()
	userDetails = User.query.filter_by(id=userPost.user_id).first()
	subject = "Microblog - Comment"
	body = "Dear {{ current_user.username }}, You have requested to email the following comment: {{userPost.body}} The comment was posted by {{userPost.user_id}} on {{userPost.timestamp}} Sincerely, The Microblog Team"
	html = "<p>Dear "+ str(current_user.username) +",</p><br/><p>You have requested to email the following comment: "+ str(userPost.body) +"</p><br/><p>The comment was posted by "+ str(userDetails.username) + " on "+ str(userPost.timestamp) +"</p><br/><br/><p>Sincerely,<br/>The Microblog Team</p>"
	send_email(subject,app.config['ADMINS'][0],[current_user.email],body,html)
	flash("Email is sent successfully.")
	return user(current_user.username)