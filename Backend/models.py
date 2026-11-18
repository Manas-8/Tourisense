from datetime import datetime
from uuid import uuid4

from extensions import db


def generate_share_id():
    return uuid4().hex


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="tourist", index=True)
    active = db.Column(db.Boolean, nullable=False, default=True)

    trips = db.relationship(
        "Trip",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    saved_places = db.relationship(
        "SavedPlace",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    checkins = db.relationship(
        "CheckIn",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Destination(TimestampMixin, db.Model):
    __tablename__ = "destinations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(180), nullable=False, unique=True, index=True)
    city = db.Column(db.String(120), nullable=False, index=True)
    state_region = db.Column(db.String(120), nullable=False, index=True)
    country = db.Column(db.String(120), nullable=False, default="India", index=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    tagline = db.Column(db.String(255), nullable=True)
    best_time_to_visit = db.Column(db.String(120), nullable=True)
    budget_info = db.Column(db.String(120), nullable=True)
    rating = db.Column(db.Numeric(3, 2), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    latitude = db.Column(db.Numeric(10, 7), nullable=True)
    longitude = db.Column(db.Numeric(10, 7), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    attractions = db.relationship(
        "Attraction",
        back_populates="destination",
        cascade="all, delete-orphan",
    )
    hotels = db.relationship(
        "Hotel",
        back_populates="destination",
        cascade="all, delete-orphan",
    )
    restaurants = db.relationship(
        "Restaurant",
        back_populates="destination",
        cascade="all, delete-orphan",
    )
    transport_options = db.relationship(
        "TransportOption",
        back_populates="destination",
        cascade="all, delete-orphan",
    )
    trips = db.relationship(
        "Trip",
        back_populates="destination",
    )
    saved_places = db.relationship(
        "SavedPlace",
        back_populates="destination",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.Index("ix_destinations_city_category", "city", "category"),
    )


class Attraction(TimestampMixin, db.Model):
    __tablename__ = "attractions"

    id = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(
        db.Integer,
        db.ForeignKey("destinations.id"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(180), nullable=False, unique=True, index=True)
    category = db.Column(db.String(80), nullable=True, index=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    latitude = db.Column(db.Numeric(10, 7), nullable=True)
    longitude = db.Column(db.Numeric(10, 7), nullable=True)
    ticket_price = db.Column(db.Numeric(10, 2), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    destination = db.relationship("Destination", back_populates="attractions")
    itinerary_activities = db.relationship(
        "ItineraryActivity",
        back_populates="attraction",
    )

    __table_args__ = (
        db.Index("ix_attractions_destination_active", "destination_id", "is_active"),
    )


class Hotel(TimestampMixin, db.Model):
    __tablename__ = "hotels"

    id = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(
        db.Integer,
        db.ForeignKey("destinations.id"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price_per_night = db.Column(db.Numeric(10, 2), nullable=True)
    rating = db.Column(db.Numeric(3, 2), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    amenities = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    destination = db.relationship("Destination", back_populates="hotels")

    __table_args__ = (
        db.UniqueConstraint("destination_id", "name", name="uq_hotels_destination_name"),
        db.Index("ix_hotels_destination_active", "destination_id", "is_active"),
    )


class Restaurant(TimestampMixin, db.Model):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(
        db.Integer,
        db.ForeignKey("destinations.id"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(150), nullable=False)
    cuisine = db.Column(db.String(120), nullable=True)
    location = db.Column(db.String(255), nullable=False)
    price_tier = db.Column(db.String(30), nullable=True)
    rating = db.Column(db.Numeric(3, 2), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    destination = db.relationship("Destination", back_populates="restaurants")

    __table_args__ = (
        db.UniqueConstraint(
            "destination_id",
            "name",
            name="uq_restaurants_destination_name",
        ),
        db.Index("ix_restaurants_destination_active", "destination_id", "is_active"),
    )


class TransportOption(TimestampMixin, db.Model):
    __tablename__ = "transport_options"

    id = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(
        db.Integer,
        db.ForeignKey("destinations.id"),
        nullable=True,
        index=True,
    )
    name = db.Column(db.String(150), nullable=False)
    transport_type = db.Column(db.String(80), nullable=True, index=True)
    route = db.Column(db.String(255), nullable=False)
    cost_from = db.Column(db.Numeric(10, 2), nullable=True)
    duration_text = db.Column(db.String(120), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    destination = db.relationship("Destination", back_populates="transport_options")

    __table_args__ = (
        db.UniqueConstraint(
            "destination_id",
            "name",
            "route",
            name="uq_transport_options_destination_name_route",
        ),
        db.Index("ix_transport_options_destination_active", "destination_id", "is_active"),
    )


class Trip(TimestampMixin, db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    destination_id = db.Column(
        db.Integer,
        db.ForeignKey("destinations.id"),
        nullable=False,
        index=True,
    )
    start_date = db.Column(db.Date, nullable=False)
    number_of_days = db.Column(db.Integer, nullable=False)
    travelers = db.Column(db.Integer, nullable=False, default=1)
    budget = db.Column(db.String(80), nullable=True)
    transport_preference = db.Column(db.String(80), nullable=True)
    accommodation_preference = db.Column(db.String(80), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)
    share_id = db.Column(
        db.String(32),
        nullable=False,
        unique=True,
        index=True,
        default=generate_share_id,
    )

    user = db.relationship("User", back_populates="trips")
    destination = db.relationship("Destination", back_populates="trips")
    interests = db.relationship(
        "TripInterest",
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    itinerary_days = db.relationship(
        "ItineraryDay",
        back_populates="trip",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.Index("ix_trips_user_destination_start", "user_id", "destination_id", "start_date"),
    )


class TripInterest(TimestampMixin, db.Model):
    __tablename__ = "trip_interests"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(
        db.Integer,
        db.ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interest = db.Column(db.String(80), nullable=False)

    trip = db.relationship("Trip", back_populates="interests")

    __table_args__ = (
        db.UniqueConstraint("trip_id", "interest", name="uq_trip_interests_trip_interest"),
    )


class ItineraryDay(TimestampMixin, db.Model):
    __tablename__ = "itinerary_days"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(
        db.Integer,
        db.ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_number = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=True)
    title = db.Column(db.String(180), nullable=False)

    trip = db.relationship("Trip", back_populates="itinerary_days")
    activities = db.relationship(
        "ItineraryActivity",
        back_populates="itinerary_day",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.UniqueConstraint("trip_id", "day_number", name="uq_itinerary_days_trip_day"),
    )


class ItineraryActivity(TimestampMixin, db.Model):
    __tablename__ = "itinerary_activities"

    id = db.Column(db.Integer, primary_key=True)
    itinerary_day_id = db.Column(
        db.Integer,
        db.ForeignKey("itinerary_days.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_order = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.Time, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    cost = db.Column(db.Numeric(10, 2), nullable=True)
    attraction_id = db.Column(
        db.Integer,
        db.ForeignKey("attractions.id"),
        nullable=True,
        index=True,
    )

    itinerary_day = db.relationship("ItineraryDay", back_populates="activities")
    attraction = db.relationship("Attraction", back_populates="itinerary_activities")
    checkins = db.relationship(
        "CheckIn",
        back_populates="activity",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "itinerary_day_id",
            "activity_order",
            name="uq_itinerary_activities_day_order",
        ),
        db.Index(
            "ix_itinerary_activities_day_attraction",
            "itinerary_day_id",
            "attraction_id",
        ),
    )


class SavedPlace(db.Model):
    __tablename__ = "saved_places"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    destination_id = db.Column(
        db.Integer,
        db.ForeignKey("destinations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    hotel_id = db.Column(
        db.Integer,
        db.ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    restaurant_id = db.Column(
        db.Integer,
        db.ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="saved_places")
    destination = db.relationship("Destination", back_populates="saved_places")

    __table_args__ = (
        db.CheckConstraint(
            "((destination_id IS NOT NULL) + "
            "(hotel_id IS NOT NULL) + "
            "(restaurant_id IS NOT NULL)) = 1",
            name="ck_saved_places_one_target",
        ),
        db.UniqueConstraint(
            "user_id",
            "destination_id",
            name="uq_saved_places_user_destination",
        ),
        db.UniqueConstraint("user_id", "hotel_id", name="uq_saved_places_user_hotel"),
        db.UniqueConstraint(
            "user_id",
            "restaurant_id",
            name="uq_saved_places_user_restaurant",
        ),
    )


class CheckIn(TimestampMixin, db.Model):
    __tablename__ = "checkins"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_id = db.Column(
        db.Integer,
        db.ForeignKey("itinerary_activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    photo_url = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    user = db.relationship("User", back_populates="checkins")
    activity = db.relationship("ItineraryActivity", back_populates="checkins")