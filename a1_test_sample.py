"""CSC148 Assignment 1: Sample tests

=== CSC148 Fall 2017 ===
Diane Horton and David Liu
Department of Computer Science,
University of Toronto

=== Module description ===
This module contains sample tests for Assignment 1.

Warning: This is an extremely incomplete set of tests!
Add your own to practice writing tests and to be confident your code is correct.

For more information on hypothesis (one of the testing libraries we're using),
please see
<http://www.teach.cs.toronto.edu/~csc148h/fall/software/hypothesis.html>.

Note: this file is for support purposes only, and is not part of your
submission.
"""
from datetime import datetime, timedelta
import os
import pygame
from pytest import approx
from bikeshare import Ride, Station
from simulation import Simulation, create_stations, create_rides


###############################################################################
# Sample tests for Task 1
###############################################################################
def test_create_stations_simple():
    """Test reading in a station from provided sample stations.json.
    """
    stations = create_stations('stations.json')
    test_id = '6023'
    assert test_id in stations

    station = stations[test_id]
    assert isinstance(station, Station)
    assert station.name == 'de la Commune / Berri'
    assert station.location == (-73.54983, 45.51086)  # NOTE: (long, lat)
    # coordinates!
    assert station.num_bikes == 18
    assert station.capacity == 39


def test_create_rides_simple():
    """Test reading in a rides file from provided sample sample_rides.csv.

    NOTE: This test relies on test_create_stations working correctly.
    """
    stations = create_stations('stations.json')
    rides = create_rides('sample_rides.csv', stations)

    # Check the first ride
    ride = rides[0]
    assert isinstance(ride, Ride)
    assert ride.start is stations['6134']
    assert ride.end is stations['6721']
    assert ride.start_time == datetime(2017, 6, 1, 7, 31, 0)
    assert ride.end_time == datetime(2017, 6, 1, 7, 54, 0)


###############################################################################
# Sample tests for Task 2
###############################################################################
def test_get_position_station():
    """Test get_position for a simple station.
    """
    stations = create_stations('stations.json')
    test_id = '6023'
    assert test_id in stations

    station = stations[test_id]
    time = datetime(2017, 9, 1, 0, 0, 0)  # Note: the time shouldn't matter.
    assert station.get_position(time) == (-73.54983, 45.51086)


def test_get_position_ride():
    """Test get_position for a simple ride.
    """
    stations = create_stations('stations.json')
    rides = create_rides('sample_rides.csv', stations)

    ride = rides[0]

    # Check ride endpoints. We use pytest's approx function to
    # avoid floating point issues.
    assert ride.get_position(ride.start_time) == approx(ride.start.location)
    assert ride.get_position(ride.end_time) == approx(ride.end.location)

    # Manually check a time during the ride.
    # Note that this ride lasts *23 minutes*, and
    # goes from (-73.562643, 45.537964) to
    # (-73.54628920555115, 45.57713595014113).
    # We're checking the position after 10 minutes have passed.
    assert (
        ride.get_position(datetime(2017, 6, 1, 7, 41, 0)) ==
        approx((-73.5555326546, 45.5549952827),
               abs=1e-5)
    )


###############################################################################
# Sample tests for Task 4
###############################################################################
def test_statistics_simple():
    """A very small test simulation.

    This runs a simulation on the sample data files
    in the time range 9:30 to 9:45, in which there's only
    one ride (the very last ride in the file).
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    sim.run(datetime(2017, 6, 1, 9, 30, 0),
            datetime(2017, 6, 1, 9, 45, 0))
    stats = sim.calculate_statistics()

    # Only one ride started!
    assert stats['max_start'] == (
        sim.all_stations['6091'].name,
        1
    )

    # Only one ride ended!
    assert stats['max_end'] == (
        sim.all_stations['6052'].name,
        1
    )

    # Many stations spent all 15 minutes (900 seconds) with
    # "low availability" or "low unoccupied".
    # We pick the ones whose names are *smallest* when compared
    # using <. Note that numbers come before letters in this ordering.

    # This station starts with only 3 bikes at the station.
    assert stats['max_time_low_availability'] == (
        '15e avenue / Masson',
        900  # 900 seconds
    )

    # This stations starts with only 1 unoccupied spot.
    assert stats['max_time_low_unoccupied'] == (
        '10e Avenue / Rosemont',
        900  # 900 seconds
    )


def test_ride_ends_outside_run():
    """Test a special case: when a ride ends outside the run period.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    sim.run(datetime(2017, 6, 1, 9, 30, 0),
            datetime(2017, 6, 1, 9, 40, 0))
    stats = sim.calculate_statistics()

    # One ride still started.
    assert stats['max_start'] == (
        sim.all_stations['6091'].name,
        1
    )

    # *No* rides were ended during the simulation time period.
    # As in the previous test, we pick the station whose name
    # is smallest when compared with <.
    assert stats['max_end'] == (
        '10e Avenue / Rosemont',
        0
    )


# ================== MY OWN TEST CASES ======================


def test_exceptional_case_1():
    """
    Exceptional Case 1: ride starts outside simulation time, and
        ends within simulation time. There is no empty or full stations.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    sim.run(datetime(2017, 7, 1, 7, 40, 0),
            datetime(2017, 7, 1, 7, 54, 0))  # end time inclusive
    stats = sim.calculate_statistics()

    assert stats["max_start"] == ("10e Avenue / Rosemont", 0)
    assert stats["max_end"] == ("Cadillac / Sherbrooke", 1)


def test_exceptional_case_3():
    """
    Exceptional Case 1: ride starts and ends outside simulation time.
     There is no empty or full stations.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    sim.run(datetime(2017, 7, 1, 7, 32, 0),
            datetime(2017, 7, 1, 7, 53, 0))
    stats = sim.calculate_statistics()

    assert stats["max_start"] == ("10e Avenue / Rosemont", 0)
    assert stats["max_end"] == ("10e Avenue / Rosemont", 0)


def test_ride_starts_outside_run_and_no_space_at_end_station():
    # Exceptional case 1 & 4.2
    # start outside runtime & no space in end_station.
    """
    Test a special case: when a ride starts outside the run period.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    sim.run(datetime(2017, 6, 1, 7, 55, 0),
            datetime(2017, 6, 1, 8, 00, 0))
    stats = sim.calculate_statistics()

    assert sim.all_stations['6034'].capacity == \
           sim.all_stations['6034'].num_bikes

    assert sim.all_stations['6034'].end == 0


def test_case_general():
    """
    General Case: ride starts and ends within simulation time, and
        there is no empty or full stations.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    sim.run(datetime(2017, 7, 1, 7, 30, 0),
            datetime(2017, 7, 1, 7, 55, 0))
    stats = sim.calculate_statistics()

    assert stats["max_start"] == ("Gascon / Rachel", 1)
    assert stats["max_end"] == ("Cadillac / Sherbrooke", 1)
    assert sim.all_stations["6134"].num_bikes == 10  # num_bikes --
    assert sim.all_stations["6721"].num_bikes == 13  # num_bikes ++


def test_exceptional_case_2():
    """
    Exceptional Case 2: ride starts within simulation time, and
        ends outside simulation time. There is no empty or full stations.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    sim.run(datetime(2017, 7, 1, 7, 31, 0),  # start time inclusive
            datetime(2017, 7, 1, 7, 40, 0))
    stats = sim.calculate_statistics()

    assert stats["max_start"] == ("Gascon / Rachel", 1)
    assert stats["max_end"] == ("10e Avenue / Rosemont", 0)


def test_exceptional_case_4_1_1():
    """
    Exceptional Case 4.1.1: ride starts within simulation time, but there is
    no bike at start station.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    # sim1 = Simulation('stations.json', 'sample_rides.csv')
    sim2 = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    # sim1.run(datetime(2017, 7, 1, 8, 0, 0),
    #         datetime(2017, 7, 1, 8, 5, 0))
    # stats1 = sim1.calculate_statistics()
    sim2.run(datetime(2017, 7, 1, 8, 6, 0),
             datetime(2017, 7, 1, 8, 10, 0))
    stats2 = sim2.calculate_statistics()

    # assert stats1["max_start"] == ("10e Avenue / Rosemont", 0)
    # assert stats1["max_end"] == ("10e Avenue / Rosemont", 0)
    assert stats2["max_start"] == ("10e Avenue / Rosemont", 0)
    assert stats2["max_end"] == ("10e Avenue / Rosemont", 0)
    assert sim2.all_stations["6159"].num_bikes == 0  # num_bikes didn't change


def test_exceptional_case_4_1_2():
    """
    Exceptional Case 4.1.2: ride starts within simulation time, but there is
    no bike at start station.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim1 = Simulation('stations.json', 'sample_rides.csv')
    # sim2 = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    sim1.run(datetime(2017, 7, 1, 8, 0, 0),
             datetime(2017, 7, 1, 8, 5, 0))
    stats1 = sim1.calculate_statistics()
    # sim2.run(datetime(2017, 7, 1, 8, 6, 0),
    #          datetime(2017, 7, 1, 8, 10, 0))
    # stats2 = sim2.calculate_statistics()

    assert stats1["max_start"] == ("10e Avenue / Rosemont", 0)
    assert stats1["max_end"] == ("10e Avenue / Rosemont", 0)
    # assert stats2["max_start"] == ("10e Avenue / Rosemont", 0)
    # assert stats2["max_end"] == ("10e Avenue / Rosemont", 0)


def test_exceptional_case_4_2_1():
    """
    Exceptional Case 4.2.1: ride starts and ends within simulation time,
    but there is space at end station.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    sim.run(datetime(2017, 7, 1, 8, 11, 0),
            datetime(2017, 7, 1, 8, 15, 0))
    stats = sim.calculate_statistics()

    assert stats["max_start"] == ("Gascon / Rachel", 1)
    assert sim.all_stations["6134"].num_bikes == 10
    assert stats["max_end"] == ("10e Avenue / Rosemont", 0)
    assert sim.all_stations["6752"].num_bikes == 27


def test_exceptional_case_4_2_2():
    """
    Exceptional Case 4.2.2: ride starts outside and ends within simulation time,
    but there is space at end station.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    sim.run(datetime(2017, 7, 1, 8, 12, 0),
            datetime(2017, 7, 1, 8, 15, 0))
    stats = sim.calculate_statistics()

    assert stats["max_start"] == ("10e Avenue / Rosemont", 0)
    assert stats["max_end"] == ("10e Avenue / Rosemont", 0)


def test_case_7():
    """
    test case 7: within simulation time period, there are more than one
    ride that either starts or ends at a same time.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    sim.run(datetime(2017, 7, 1, 8, 16, 0),
            datetime(2017, 7, 1, 8, 17, 0))
    stats = sim.calculate_statistics()

    assert stats["max_start"] == ("Gascon / Rachel", 5)
    assert stats["max_end"] == ("Cadillac / Sherbrooke", 5)


def test_case_7_and_4_1():
    """
    test case 7 and 4.1: multiple bikes start at same time, but there is not
    enough bike at start station. In this case, there are 3 bikes and 4 rides
    starts.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    sim.run(datetime(2017, 7, 1, 8, 18, 0),
            datetime(2017, 7, 1, 8, 19, 0))
    stats = sim.calculate_statistics()

    assert stats["max_start"] == ("Marquette / Rachel", 3)
    assert stats["max_end"] == ("Cadillac / Sherbrooke", 3)


def test_case_7_and_4_2():
    """
    test case 7 and 4.2: multiple bikes start at same time, but there is not
    enough space at end station. In this case, there are 3 space and 4 rides
    ends.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Ignore this line
    sim = Simulation('stations.json', 'sample_rides.csv')
    pygame.event.post(pygame.event.Event(pygame.QUIT, {}))  # Ignore this line

    # This last ride in the sample_rides.csv file now begins
    # during the simulation run, but ends after the run.
    sim.run(datetime(2017, 7, 1, 8, 20, 0),
            datetime(2017, 7, 1, 8, 21, 0))
    stats = sim.calculate_statistics()

    assert stats["max_start"] == ("Gascon / Rachel", 4)
    assert stats["max_end"] == ("de Bordeaux / Jean-Talon", 3)


if __name__ == '__main__':
    import pytest

    pytest.main(['a1_test_sample.py'])
