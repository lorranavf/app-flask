from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from app import app, db
from app.main import bp
from app.main.forms import EditProfileForm, EmptyForm, PostForm
from app.models import User, Post

@bp.route('/')
def root():
    return render_template('root.html')


@bp.route('/user/<username>')
@login_required
def user_page(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template('userpage.html', user=user, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.firstname = form.firstname.data
        current_user.lastname = form.lastname.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.user_page', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        current_user.firstname = form.firstname.data
        current_user.lastname = form.lastname.data
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.root'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('main.user_page', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('main.user_page', username=username))
    else:
        return redirect(url_for('main.root'))

@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.root'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('main.user_page', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('main.user_page', username=username))
    else:
        return redirect(url_for('main.root'))


@bp.route('/posts', methods=['GET', 'POST'])
@login_required
def posts():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('main.posts'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.posts', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.posts', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('posts.html', form=form, posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('explore.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)
