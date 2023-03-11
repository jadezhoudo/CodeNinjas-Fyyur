# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
import babel.dates
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from sqlalchemy import String, cast, func, or_
from datetime import datetime

from forms import ArtistForm, ShowForm, VenueForm

# from forms import *
# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TO DO: connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

performances = db.Table('Show',
                        db.Column('id', db.Integer, primary_key=True),
                        db.Column('venue_id', db.Integer, db.ForeignKey(
                            'Venue.id'), nullable=False),
                        db.Column('artist_id', db.Integer, db.ForeignKey(
                            'Artist.id'),  nullable=False),
                        db.Column('start_time', db.DateTime, nullable=False)
                        )


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    artists = db.relationship(
        'Artist', secondary=performances, backref=db.backref('venues', lazy=True))

    def __repr__(self):
        return '<Venue{}>'.format(self.name)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    website = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    seeking_description = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data_venues = db.session.query(Venue.id,
                                   Venue.name,
                                   Venue.city,
                                   Venue.state,
                                   func.count(performances.c.id).filter(
                                       performances.c.start_time > datetime.now())
                                   .label('upcoming_shows')).outerjoin(performances, performances.c.venue_id == Venue.id).group_by(Venue.id).all()
    places = db.session.query(Venue.city, Venue.state).group_by(
        Venue.city, Venue.state).all()
    data = []
    for i in places:
        venues = [ve for ve in data_venues if ve.city ==
                  i.city and ve.state == i.state]
        data_formated = {
            "city": i.city,
            "state": i.state,
            "venues": venues
        }
        data.append(data_formated)
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(or_(Venue.name.ilike(f'%{search_term}%'), Venue.city.ilike(
        f'%{search_term}%'), Venue.state.ilike(f'%{search_term}%'))).all()
    upcoming_show = db.session.query(performances.c.venue_id, func.count(performances.c.id).label('num_upcoming_shows'))\
        .filter(performances.c.start_time > datetime.now())\
        .group_by(performances.c.venue_id).all()
    response = {
        "count": len(venues),
        "data": [{
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": [x.num_upcoming_shows for x in upcoming_show if x.venue_id == venue.id],
        } for venue in venues]
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)

    venue_data = {
        'id': venue.id,
        'name': venue.name,
        'genres': venue.genres,
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
    }

    show_query = db.session.query(performances, Artist.name.label('name'),
                                  Artist.image_link.label('image_link')).join(Artist, performances.c.artist_id == Artist.id).filter(
        performances.c.venue_id == venue_id).all()

    upcoming_shows = []
    past_shows = []
    for show in show_query:
        show_data = {
            'artist_id': show.artist_id,
            'artist_name': show.name,
            'artist_image_link': show.image_link,
            'start_time': str(show.start_time)
        }
        if show.start_time > datetime.now():
            upcoming_shows.append(show_data)
        else:
            past_shows.append(show_data)

    venue_data['upcoming_shows'] = upcoming_shows
    venue_data['upcoming_shows_count'] = len(upcoming_shows)
    venue_data['past_shows'] = past_shows
    venue_data['past_shows_count'] = len(past_shows)
    return render_template('pages/show_venue.html', venue=venue_data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        new_venue = Venue(
            name=request.form["name"],
            city=request.form["city"],
            state=request.form["state"],
            address=request.form["address"],
            phone=request.form["phone"],
            genres=request.form.getlist("genres"),
            image_link=request.form["image_link"],
            facebook_link=request.form["facebook_link"],
            website=request.form["website_link"],
            seeking_talent=True if "seeking_talent" in request.form else False,
            seeking_description=request.form["seeking_description"],
        )
        db.session.add(new_venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except Exception as exception:
        db.session.rollback()
        print(exception)
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
        flash('Venue was successfully deleted!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue could not be deleted.')
    finally:
        db.session.close()
    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    data = db.session.query(Artist)
    print(data)
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    artists = Artist.query.filter(or_(Artist.name.ilike(f'%{search_term}%'), Artist.city.ilike(
        f'%{search_term}%'), Artist.state.ilike(f'%{search_term}%'))).all()
    upcoming_show = db.session.query(performances.c.artist_id, func.count(performances.c.id).label('num_upcoming_shows'))\
        .filter(performances.c.start_time > datetime.now())\
        .group_by(performances.c.artist_id).all()
    response = {
        "count": len(artists),
        "data": [{
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": [x.num_upcoming_shows for x in upcoming_show if x.artist_id == artist.id],
        } for artist in artists]
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist = Artist.query.get(artist_id)

    artist_data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "seeking_venue": artist.seeking_venue,
        "image_link": artist.image_link,
    }

    print("artist.genres ===> ", artist.genres)

    show_query = db.session.query(performances, Venue.name.label('name'),
                                  Venue.image_link.label('image_link')).join(Venue, performances.c.venue_id == Venue.id).filter(
        performances.c.artist_id == artist_id).all()

    print(show_query)
    upcoming_shows = []
    past_shows = []
    for show in show_query:
        show_data = {
            "venue_id": show.venue_id,
            "venue_name": show.name,
            "venue_image_link": show.image_link,
            "start_time": str(show.start_time)
        }
        if show.start_time > datetime.now():
            upcoming_shows.append(show_data)
        else:
            past_shows.append(show_data)

    artist_data['upcoming_shows'] = upcoming_shows
    artist_data['upcoming_shows_count'] = len(upcoming_shows)
    artist_data['past_shows'] = past_shows
    artist_data['past_shows_count'] = len(past_shows)

    #

    # data1 = {
    #     "id": 4,
    #     "name": "Guns N Petals",
    #     "genres": ["Rock n Roll"],
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "326-123-5000",
    #     "website": "https://www.gunsnpetalsband.com",
    #     "facebook_link": "https://www.facebook.com/GunsNPetals",
    #     "seeking_venue": True,
    #     "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    #     "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    #     "past_shows": [{
    #             "venue_id": 1,
    #             "venue_name": "The Musical Hop",
    #             "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    #             "start_time": "2019-05-21T21:30:00.000Z"
    #     }],
    #     "upcoming_shows": [],
    #     "past_shows_count": 1,
    #     "upcoming_shows_count": 0,
    # }
    # data2 = {
    #     "id": 5,
    #     "name": "Matt Quevedo",
    #     "genres": ["Jazz"],
    #     "city": "New York",
    #     "state": "NY",
    #     "phone": "300-400-5000",
    #     "facebook_link": "https://www.facebook.com/mattquevedo923251523",
    #     "seeking_venue": False,
    #     "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    #     "past_shows": [{
    #             "venue_id": 3,
    #             "venue_name": "Park Square Live Music & Coffee",
    #             "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #             "start_time": "2019-06-15T23:00:00.000Z"
    #     }],
    #     "upcoming_shows": [],
    #     "past_shows_count": 1,
    #     "upcoming_shows_count": 0,
    # }
    # data3 = {
    #     "id": 6,
    #     "name": "The Wild Sax Band",
    #     "genres": ["Jazz", "Classical"],
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "432-325-5432",
    #     "seeking_venue": False,
    #     "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #     "past_shows": [],
    #     "upcoming_shows": [{
    #             "venue_id": 3,
    #             "venue_name": "Park Square Live Music & Coffee",
    #             "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #             "start_time": "2035-04-01T20:00:00.000Z"
    #     }, {
    #         "venue_id": 3,
    #         "venue_name": "Park Square Live Music & Coffee",
    #         "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #         "start_time": "2035-04-08T20:00:00.000Z"
    #     }, {
    #         "venue_id": 3,
    #         "venue_name": "Park Square Live Music & Coffee",
    #         "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #         "start_time": "2035-04-15T20:00:00.000Z"
    #     }],
    #     "past_shows_count": 0,
    #     "upcoming_shows_count": 3,
    # }
    # data = list(filter(lambda d: d['id'] ==
    #             artist_id, [data1, data2, data3]))[0]
    # print("artist_data ==> ", artist_data)
    return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    # artist = {
    #     "id": 4,
    #     "name": "Guns N Petals",
    #     "genres": ["Rock n Roll"],
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "326-123-5000",
    #     "website": "https://www.gunsnpetalsband.com",
    #     "facebook_link": "https://www.facebook.com/GunsNPetals",
    #     "seeking_venue": True,
    #     "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    #     "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    # }
    # # TODO: populate form with fields from artist with ID <artist_id>
    # return render_template('forms/edit_artist.html', form=form, artist=artist)
    artist = Artist.query.get(artist_id)
    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website_link.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    # return redirect(url_for('show_artist', artist_id=artist_id))
    form = ArtistForm(request.form)
    artist = Artist.query.get(artist_id)
    print("form.name.data ===> ", form.name.data)
    if form.validate():
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.image_link = form.image_link.data
        artist.facebook_link = form.facebook_link.data
        artist.website = form.website_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    else:
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be updated.')
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = {
        "id": 1,
        "name": "The Musical Hop",
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": "1015 Folsom Street",
        "city": "San Francisco",
        "state": "CA",
        "phone": "123-123-1234",
        "website": "https://www.themusicalhop.com",
        "facebook_link": "https://www.facebook.com/TheMusicalHop",
        "seeking_talent": True,
        "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
        new_artist = Artist(
            name=request.form["name"],
            city=request.form["city"],
            state=request.form["state"],
            phone=request.form["phone"],
            genres=request.form.getlist("genres"),
            image_link=request.form["image_link"],
            facebook_link=request.form["facebook_link"],
            website=request.form["website_link"],
            seeking_venue=True if "seeking_venue" in request.form else False,
            seeking_description=request.form["seeking_description"],
        )
        db.session.add(new_artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')

    except Exception as exception:
        db.session.rollback()
        print(exception)
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    dataQuery = db.session.query(performances.c.venue_id, Venue.name.label('venue_name'), Artist.name.label('arist_name'), performances.c.artist_id, performances.c.start_time,
                                 Artist.image_link.label('artist_image_link')).join(Venue, performances.c.venue_id == Venue.id).join(Artist, performances.c.artist_id == Artist.id).all()
    print(dataQuery)
    for d in dataQuery:
        print(d)
        dt = {
            "start_time": str(d.start_time),
            "venue_id": str(d.venue_id),
            "artist_id": str(d.artist_id),
            "venue_name": d.venue_name,
            "arist_name": d.arist_name,
            "artist_image_link": d.artist_image_link,
        }
        data.append(dt)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    # on successful db insert, flash success
    # flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    # return render_template('pages/home.html')

    try:
        venue_id = request.form.get('venue_id')
        artist_id = request.form.get('artist_id')
        start_time = datetime.strptime(
            request.form.get('start_time'), '%Y-%m-%d %H:%M:%S')
        show = performances(venue_id=venue_id,
                            artist_id=artist_id, start_time=start_time)
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except Exception as exception:
        db.session.rollback()
        print(exception)
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
# if __name__ == '__main__':
#     app.run()
if __name__ == '__main__':
    app.run(port=3000, debug=True, host="0.0.0.0")

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
