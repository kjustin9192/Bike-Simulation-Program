"""Assignment 1 - Bike-share objects

=== CSC148 Fall 2017 ===
Diane Horton and David Liu
Department of Computer Science,
University of Toronto


=== Module Description ===

This file contains the Station and Ride classes, which store the data for the
objects in this simulation.

There is also an abstract Drawable class that is the superclass for both
Station and Ride. It enables the simulation to visualize these objects in
a graphical window.
"""
from datetime import datetime
from typing import Tuple


# Sprite files
STATION_SPRITE = 'stationsprite.png'
RIDE_SPRITE = 'bikesprite.png'


class Drawable:
    """A base class for objects that the graphical renderer can be drawn.

    === Public Attributes ===
    sprite:
        The filename of the image to be drawn for this object.
    """
    sprite: str

    def __init__(self, sprite_file: str) -> None:
        """Initialize this drawable object with the given sprite file.
        """
        self.sprite = sprite_file

    def get_position(self, time: datetime) -> Tuple[float, float]:
        """Return the (long, lat) position of this object at the given time.
        """
        raise NotImplementedError


class Station(Drawable):
    """A Bixi station.

    === Public Attributes ===
    capacity: str
        The total number of bikes the station can store
    location: Tuple[float, float]
        The location of the station in long/lat coordinates
    name: str
        Name of the station
    num_bikes: int
        Current number of bikes at the station
    start: int
        The number of rides that started at this station during the simulation.
    end: int
        The number of rides that ended at this station during the simulation
    tla: int
        Stands for 'Total Low Availability'.
        Total amount of time during the simulation, in seconds,
        that the station spent with at most five bikes available.
    tlu: int
        Stands for 'Total Low Unoccupied'.
        Total amount of time during the simulation, in seconds,
        that the station spent with at most five unoccupied spots.

    === Representation Invariants ===
    - 0 <= num_bikes <= capacity
    """
    name: str
    location: Tuple[float, float]
    capacity: int
    num_bikes: int
    start: int
    end: int
    tla: int  # time_low_availability
    tlu: int  # time_low_unoccupied

    def __init__(self, pos: Tuple[float, float], cap: int,
                 num_bikes: int, name: str) -> None:
        """Initialize a new station.
        """
        Drawable.__init__(self, STATION_SPRITE)
        self.location = pos
        self.capacity = cap
        self.num_bikes = num_bikes
        self.name = name
        self.start = self.end = self.tla = self.tlu = 0

    def get_position(self, time: datetime) -> Tuple[float, float]:
        """Return the (long, lat) position of this station for the given time.

        Note that the station's location does *not* change over time.
        The <time> parameter is included only because we should not change
        the header of an overridden method.
        """

        return self.location


class Ride(Drawable):
    """A ride using a Bixi bike.

    === Attributes ===
    start:
        the station where this ride starts
    end:
        the station where this ride ends
    start_time:
        the time this ride starts
    end_time:
        the time this ride ends

    === Representation Invariants ===
    - start_time < end_time
    """
    start: Station
    end: Station
    start_time: datetime
    end_time: datetime

    def __init__(self, start: Station, end: Station,
                 times: Tuple[datetime, datetime]) -> None:
        """Initialize a ride object with the given start and end information.
        """
        Drawable.__init__(self, RIDE_SPRITE)

        self.start, self.end = start, end
        self.start_time, self.end_time = times[0], times[1]

    def get_position(self, time: datetime) -> Tuple[float, float]:
        """Return the position of this ride for the given time.

        A ride travels in a straight line between its start and end stations
        at a constant speed.
        """
        start_long: float = self.start.get_position(time)[0]
        start_lat: float = self.start.get_position(time)[1]
        end_long: float = self.end.get_position(time)[0]
        end_lat: float = self.end.get_position(time)[1]

        long_diff = end_long - start_long
        lat_diff = end_lat - start_lat
        time_diff = time - self.start_time
        time_total_interval = self.end_time - self.start_time

        multiply_factor = time_diff.seconds/time_total_interval.seconds

        if time <= self.start_time:
            return (start_long, start_lat)
        elif time >= self.end_time:
            return (end_long, end_lat)
        else:
            long = start_long + (multiply_factor * long_diff)
            lat = start_lat + (multiply_factor * lat_diff)
            return (long, lat)


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'typing',
            'datetime'
        ],
        'max-attributes': 15
    })
