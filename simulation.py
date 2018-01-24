"""Assignment 1 - Simulation

=== CSC148 Fall 2017 ===
Diane Horton and David Liu
Department of Computer Science,
University of Toronto


=== Module Description ===

This file contains the Simulation class, which is the main class for your
bike-share simulation.

At the bottom of the file, there is a sample_simulation function that you
can use to try running the simulation at any time.
"""
import csv
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple, Optional

from bikeshare import Ride, Station
from container import PriorityQueue
from visualizer import Visualizer

# Datetime format to parse the ride data
DATETIME_FORMAT = '%Y-%m-%d %H:%M'


class Simulation:
    """Runs the core of the simulation through time.

    === Attributes ===
    all_rides:
        A list of all the rides in this simulation.
        Note that not all rides might be used, depending on the timeframe
        when the simulation is run.
    all_stations:
        A dictionary containing all the stations in this simulation.
    visualizer:
        A helper class for visualizing the simulation.
    active_rides:
        A list of ride instances that are active(i.e. on the way)
        during simulation time period.
    priorityqueue:
        A queue of items that contains Event instances.

    """
    all_stations: Dict[str, Station]
    all_rides: List[Ride]
    visualizer: Visualizer
    active_rides: List[Ride]
    priorityqueue: PriorityQueue

    def __init__(self, station_file: str, ride_file: str) -> None:
        """Initialize this simulation with the given configuration settings.
        """
        self.visualizer = Visualizer()
        self.all_stations = create_stations(station_file)
        self.all_rides = create_rides(ride_file, self.all_stations)
        self.active_rides = []
        self.priorityqueue = PriorityQueue()

    def run(self, start: datetime, end: datetime) -> None:
        """Run the simulation from <start> to <end>.

        === Representation Invariant ===
        - Time step for each iteration in simulation run is fixed to 1 minute.
        - The parameter <start> is smaller than <end>

        === Precondition ===
        - ride times from sample_rides.csv file are given in minutes only.
            i.e. datetime_variable.second == 0
                 datetime_variable.microsecond == 0
        - Ride's start time is smaller than its end time
        """
        current_time = start
        step = timedelta(minutes=1)  # Each iteration spans one minute of time

        # 1. Add "ride start" event to priority queue for each ride that occurs
        #    during the simulation time period.
        # 2. Add "ride end" event to priority queue for each ride, where start
        #    occurs before simulation time period and end occurs during
        #    the simulation time period.
        # It means that events that start outside simulation time period and
        # ends within or outside simulation time period won't be considered.
        for ride_ in self.all_rides:
            if start <= ride_.start_time <= end:
                ride_start_event = RideStartEvent(
                    self, ride_.start_time, ride_
                )
                self.priorityqueue.add(ride_start_event)
            if (ride_.start_time < start) and (ride_.end_time >= start):
                ride_end_event = RideEndEvent(
                    self, ride_.end_time, ride_
                )
                self.active_rides.append(ride_)
                self.priorityqueue.add(ride_end_event)

        while current_time <= end:  # start_time & end_time inclusive
            self._update_active_rides(current_time)
            # self._update_active_rides_fast(current_time)

            # availability and low_occupancy are only checked within intervals.
            if current_time < end:
                self._update_stat_low_availability_unoccupied()

            render_list = list(self.all_stations.values()) + self.active_rides
            self.visualizer.render_drawables(render_list, current_time)
            current_time += step

        # The code below will keep the visualization window open until you
        # close it by pressing the 'X'.
        while True:
            if self.visualizer.handle_window_events():
                return  # Stop the simulation

    def _update_active_rides(self, time: datetime) -> None:
        """Update this simulation's list of active_rides and statistics
         for the given time.

         Change stats for
            - 'max_start': Yes
            - 'max_end': Yes
            - 'max_time_low_availability': No
            - 'max_time_low_unoccupied': No

        If a ride starts from a station at a given time,
            - 'start' attribute of station is incremented by 1.
            - 'num_bikes' attribute of station is decremented by 1.
        If a ride ends at a station at a given time,
            - 'end' attribute of station is incremented by 1.
            - 'num_bikes' attribute of station is incremented by 1.

        * Event Anomalies
            - If there are no bikes at a station when a ride starts,
              this event is completely ignored.
            - If there is no space at a station when a ride ends,
              the ride is removed from active_rides, but the stats
              are not counted.
        """

        for ride in self.all_rides:
            # If a ride starts when its start station is empty, we should
            # completely ignore this case. Therefore, remove this ride from
            # all_rides.
            if (ride.start.num_bikes <= 0) and \
                    (ride.start_time <= time <= ride.end_time) and \
                    (ride not in self.active_rides):
                # if station is empty
                self.all_rides.remove(ride)
                continue

            # Add ride to active_rides when it starts.
            if (ride.start_time <= time <= ride.end_time) and \
                    (ride not in self.active_rides):
                self.active_rides.append(ride)
            # Remove ride from active_rides when it ends.
            if (time > ride.end_time) and (ride in self.active_rides):
                self.active_rides.remove(ride)

            # Stats (start, end, num_bikes)
            if ride.start_time == time and ride.start.num_bikes > 0:
                ride.start.start += 1
                ride.start.num_bikes -= 1
            if ride.end_time == time and ride.end.num_bikes < ride.end.capacity:
                ride.end.end += 1
                ride.end.num_bikes += 1

    def _update_active_rides_fast(self, time: datetime) -> None:
        """Update this simulation's list of active_rides and statistics
        for the given time, using Priority Queue.

        Change stats for
            - 'max_start': Yes
            - 'max_end': Yes
            - 'max_time_low_availability': No
            - 'max_time_low_unoccupied': No

        If a ride starts from a station at a given time,
            - 'start' attribute of station is incremented by 1.
            - 'num_bikes' attribute of station is decremented by 1.
        If a ride ends at a station at a given time,
            - 'end' attribute of station is incremented by 1.
            - 'num_bikes' attribute of station is incremented by 1.

        * Event Anomalies
            - If there are no bikes at a station when a ride starts,
              this event is completely ignored.
            - If there is no space at a station when a ride ends,
              the ride is removed from active_rides, but the stats
              are not counted.
        """
        # Do nothing if priorityqueue is empty.
        # Iterates through the PQ events until the event time is after
        # the current simulation time. This is to take into account
        # a potential situation where there are 2 events with the
        # same time in the queue.
        if self.priorityqueue.is_empty():
            return None
        while True:
            event = self.priorityqueue.remove()
            if time < event.time:
                self.priorityqueue.add(event)
                break
            else:
                event.process()
                if self.priorityqueue.is_empty():
                    break

    def calculate_statistics(self) -> Dict[str, Tuple[str, float]]:
        """Return a dictionary containing statistics for this simulation.

        The returned dictionary has exactly four keys, corresponding
        to the four statistics tracked for each station:
          - 'max_start'
          - 'max_end'
          - 'max_time_low_availability'
          - 'max_time_low_unoccupied'

        The corresponding value of each key is a tuple of two elements,
        where the first element is the name (NOT id) of the station that has
        the maximum value of the quantity specified by that key,
        and the second element is the value of that quantity.

        For example, the value corresponding to key 'max_start' should be the
        name of the station with the most number of rides started at that
        station, and the number of rides that started at that station.
        """

        # initialization of finding maximum values.
        # max_tla for max_time_low_availability
        # max_tlu for max_time_low_unoccupied
        max_start = max_end = max_tla = max_tlu = 0

        # find the maximum value for each variable max_start, ... , max_tlu
        for id_ in self.all_stations:
            if self.all_stations[id_].start > max_start:
                max_start = self.all_stations[id_].start
            if self.all_stations[id_].end > max_end:
                max_end = self.all_stations[id_].end
            if self.all_stations[id_].tla > max_tla:
                max_tla = self.all_stations[id_].tla
            if self.all_stations[id_].tlu > max_tlu:
                max_tlu = self.all_stations[id_].tlu

        # find the name of station who comes first in alphabetical order.
        list_max_start: List[str] = []
        list_max_end: List[str] = []
        list_max_tla: List[str] = []
        list_max_tlu: List[str] = []
        for id_ in self.all_stations:
            temp_station = self.all_stations[id_]
            if temp_station.start == max_start:
                list_max_start.append(temp_station.name)
            if temp_station.end == max_end:
                list_max_end.append(temp_station.name)
            if temp_station.tla == max_tla:
                list_max_tla.append(temp_station.name)
            if temp_station.tlu == max_tlu:
                list_max_tlu.append(temp_station.name)
        return {
            'max_start': (sorted(list_max_start)[0], max_start),
            'max_end': (sorted(list_max_end)[0], max_end),
            'max_time_low_availability': (
                sorted(list_max_tla)[0], max_tla),
            'max_time_low_unoccupied': (
                sorted(list_max_tlu)[0], max_tlu)
        }

    def _update_stat_low_availability_unoccupied(self) -> None:
        """ A helper method for calculating statistics.

        It changes stats for
            - 'max_start': No
            - 'max_end': No
            - 'max_time_low_availability': Yes
            - 'max_time_low_unoccupied': Yes

        - 'tla' attribute of station is incremented by 60 seconds if the
          station has at most five bikes available at a given time.
        - 'tlu' attribute of station is incremented by 60 seconds if the
           station has at most five spaces available at a given time.
        """
        for id_ in self.all_stations:
            station = self.all_stations[id_]

            # time_low_availability
            if station.num_bikes <= 5:
                station.tla += 60  # 1 minute -> 60 second

            # time_low_unoccupied
            if (station.capacity - station.num_bikes) <= 5:
                station.tlu += 60  # 1 minute -> 60 second


def create_stations(stations_file: str) -> Dict[str, 'Station']:
    """Return the stations described in the given JSON data file.

    Each key in the returned dictionary is the id number of the station,
    and each value is the corresponding Station object.

    === Precondition ===
    stations_file matches the format specified in the assignment handout.

    This function should be called *before* _read_rides because the
    rides CSV file refers to station ids.
    """
    # Read in raw data using the json library.
    with open(stations_file) as file:
        raw_stations = json.load(file)

    stations = {}
    for s in raw_stations['stations']:
        # Extract the relevant fields from the raw station JSON.
        # s is a dictionary with the keys 'n', 's', 'la', 'lo', 'da', and 'ba'
        # as described in the assignment handout.
        # NOTE: all of the corresponding values are strings, and so you need
        # to convert some of them to numbers explicitly using int() or float().
        # s['da']+s['ba'] = total number of bike spots in station

        stn = Station((s['lo'], s['la']), s['da'] + s['ba'], s['da'], s['s'])
        stations[s['n']] = stn

    return stations


def create_rides(rides_file: str,
                 stations: Dict[str, 'Station']) -> List['Ride']:
    """Return the rides described in the given CSV file.

    Lookup the station ids contained in the rides file in <stations>
    to access the corresponding Station objects.

    Ignore any ride whose start or end station is not present in <stations>.

    === Precondition ===
    rides_file matches the format specified in the assignment handout.
    """
    rides = []
    with open(rides_file) as file:
        for line in csv.reader(file):
            # line is a list of strings, following the format described
            # in the assignment handout.
            #
            # Convert between a string and a datetime object
            # using the function datetime.strptime and the DATETIME_FORMAT
            # constant we defined above. Example:
            # >>> datetime.strptime('2017-06-01 8:00', DATETIME_FORMAT)
            # datetime.datetime(2017, 6, 1, 8, 0)
            if line[1] in stations and line[3] in stations:
                t_start = datetime.strptime(line[0], DATETIME_FORMAT)
                t_end = datetime.strptime(line[2], DATETIME_FORMAT)

                rd = Ride(
                    stations[line[1]], stations[line[3]], (t_start, t_end)
                )
                rides.append(rd)
    return rides


class Event:
    """An event in the bike share simulation.

    An event is an object representing some sort of change to the
    state of the simulation.
    Events are ordered by their timestamp.

    === Attributes ===
    simulation:
        Simulation where this event occurs. It is needed for an event to
        modify the state of simulation.
    time:
        Time that the event occurs.
    ride:
        An instance of class Ride. The event occurs when a ride starts or ends.
    """

    simulation: 'Simulation'
    time: datetime
    ride: Optional['Ride']

    def __init__(self, simulation: 'Simulation', time: datetime) -> None:
        """Initialize a new event."""
        self.simulation = simulation
        self.time = time

    def __lt__(self, other: 'Event') -> bool:
        """Return whether this event is less than <other>.

        Events are ordered by their timestamp.
        """
        return self.time < other.time

    def __le__(self, other: 'Event') -> bool:
        """Return whether this event is less than or equal to <other>.

        Events are ordered by their timestamp.
        """
        return self.time <= other.time

    def process(self) -> List['Event']:
        """Process this event by updating the state of the simulation.

        Return a list of new events spawned by this event.
        """
        raise NotImplementedError


class RideStartEvent(Event):
    """An event corresponding to the start of a ride.

    An event is an object representing some sort of change to the
    state of the simulation. Events are ordered by their timestamp.

    === Attributes ===
    simulation:
        Simulation where this event occurs. It is needed for an event to
        modify the state of simulation.
    time:
        Time that the event occurs.
    ride:
        An instance of class Ride. This RideStartEvent occurs when a ride
        starts from its stating station.
    end_event:
        An instance of class RideEndEvent. It is initiated and passed to
        priority queue of simulation when process method is called.

    """
    end_event: 'Event'

    def __init__(self, simulation: 'Simulation', time: datetime,
                 ride: 'Ride' = None) -> None:
        """Initialize a new event."""
        Event.__init__(self, simulation, time)
        self.ride = ride
        self.end_event = RideEndEvent(simulation, ride.end_time, ride)

    def process(self) -> List['Event']:
        """
        Process this event and update the state of the simulation.

        Add ride attribute to active_rides list of simulation.
        Also, add an instance of RideEndEvent class to priority queue.
        Finally, change some statistics.

        Return a list of new events spawned by this event. List is empty
        if there are no new events.

        === Precondition ===
        ride is not None
        """
        list_new_event = []
        # Stats (start, num_bikes)
        station = self.ride.start
        if station.num_bikes > 0:
            station.start += 1
            station.num_bikes -= 1
            self.simulation.priorityqueue.add(self.end_event)
            self.simulation.active_rides.append(self.ride)
        list_new_event.append(self.end_event)
        return list_new_event


class RideEndEvent(Event):
    """An event corresponding to the end of a ride.

    An event is an object representing some sort of change to the
    state of the simulation. Events are ordered by their timestamp.

    === Attributes ===
    simulation:
        Simulation where this event occurs. It is needed for an event to
        modify the state of simulation.
    time:
        Time that the event occurs.
    ride:
        An instance of class Ride. This RideEndEvent occurs when a ride
        ends at its ending station.
    """

    def __init__(self, simulation: 'Simulation', time: datetime,
                 ride: 'Ride' = None) -> None:
        Event.__init__(self, simulation, time)
        self.ride = ride

    def process(self) -> List['Event']:
        """
        Process this event and update the state of the simulation.

        Remove ride attribute from active_rides list of simulation.
        And change some statistics.

        Return a list of new events spawned by this event. List is empty
        if there are no new events.

        === Precondition ===
        ride is not None
        """
        self.simulation.active_rides.remove(self.ride)

        list_new_event = []
        # Stats (end, num_bikes)
        station = self.ride.end
        if station.num_bikes < station.capacity:
            station.end += 1
            station.num_bikes += 1
        return list_new_event


def sample_simulation() -> Dict[str, Tuple[str, float]]:
    """Run a sample simulation. For testing purposes only.

    Return statistics of simulation in dictionary type.
    For more information about statistics, please refer to
        -> Simulation.calculate_statistics()
    """
    sim = Simulation('stations.json', 'sample_rides.csv')
    sim.run(datetime(2017, 6, 1, 8, 0, 0),
            datetime(2017, 6, 1, 9, 0, 0))
    return sim.calculate_statistics()


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-io': ['create_stations', 'create_rides'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'typing',
            'csv', 'datetime', 'json',
            'bikeshare', 'container', 'visualizer'
        ]
    })
    print(sample_simulation())
