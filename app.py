from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devsecret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
wishlist_table = db.Table(
    'wishlist',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('game_id', db.Integer, db.ForeignKey('game.id'))
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    wishlist = db.relationship(
        'Game', secondary=wishlist_table, backref='wishers')


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(200), default='')

# Simple helpers


def current_user():
    uid = session.get('user_id')
    return User.query.get(uid) if uid else None

# CLI seed command to populate DB


@app.cli.command('seed')
def seed():
    db.drop_all()
    db.create_all()
    g1 = Game(title='Neon Skies', price=9.99,
              description='Fast-paced aerial shooter', tags='arcade;shooter')
    g2 = Game(title='Mystic Farm', price=14.99,
              description='Relaxing farming sim', tags='simulation;casual')
    g3 = Game(title='Deep Rift', price=24.99,
              description='Dark sci-fi RPG', tags='rpg;adventure')
    db.session.add_all([g1, g2, g3])
    u = User(username='alice')
    db.session.add(u)
    db.session.commit()
    print('Seeded DB')

# Routes


@app.route('/')
def index():
    games = Game.query.all()
    user = current_user()
    return render_template('index.html', games=games, user=user)


@app.route('/game/<int:game_id>')
def game_detail(game_id):
    g = Game.query.get_or_404(game_id)
    user = current_user()
    in_wishlist = False
    if user:
        in_wishlist = g in user.wishlist
    return render_template('game.html', game=g, in_wishlist=in_wishlist, user=user)


@app.route('/toggle_wishlist/<int:game_id>')
def toggle_wishlist(game_id):
    user = current_user()
    if not user:
        flash('Please login to use wishlist')
        return redirect(url_for('login', next=url_for('game_detail', game_id=game_id)))
    g = Game.query.get_or_404(game_id)
    if g in user.wishlist:
        user.wishlist.remove(g)
    else:
        user.wishlist.append(g)
    db.session.commit()
    return redirect(url_for('game_detail', game_id=game_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if not username:
            flash('Provide a username')
            return redirect(url_for('login'))
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        session['user_id'] = user.id
        return redirect(request.args.get('next') or url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Ensure DB exists for local dev
    if not os.path.exists('store.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
