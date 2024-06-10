import threading
import time
import random
import queue
import matplotlib.pyplot as plt
import numpy as np

# Constants
NUM_TELLERS = 3
QUEUE_SIZE = 100
MAX_SERVICE_TIME = 12
MIN_SERVICE_TIME = 2
QUANTUM_TIME = 2
CUSTOMER_LIMIT = 100

customer_queues = {
    1: queue.Queue(QUEUE_SIZE),
    2: queue.PriorityQueue(QUEUE_SIZE),
    3: queue.Queue(QUEUE_SIZE)
}

class LimitCross(Exception):
    pass

# Statistics
arrival_times = {}
service_times = {}
completion_times = {}
remaining_service_times = {}

fcfs_turnaround_times = []
sjf_preemptive_turnaround_times = []
rr_turnaround_times = []

fcfs_waiting_times = []
sjf_preemptive_waiting_times = []
rr_waiting_times = []

fcfs_response_times = []
sjf_preemptive_response_times = []
rr_response_times = []

responded = []

# Lock for thread-safe updates to statistics
lock = threading.Lock()

# Flag to stop threads
stop_event = threading.Event()

def timeConverter(t1):
    local_time = time.localtime(t1)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    return formatted_time

def empty_queue(q):
    while not q.empty():
        q.get()

def customer_arrival(queue_type):
    customer_id = 1
    while not stop_event.is_set():
        service_time = random.randint(MIN_SERVICE_TIME, MAX_SERVICE_TIME)
        arrival_time = time.time()
        with lock:
            arrival_times[customer_id] = arrival_time
            service_times[customer_id] = service_time
            remaining_service_times[customer_id] = service_time
        print(f"Customer {customer_id} enters the Queue with service time {service_time} at {timeConverter(arrival_time)}, No of customers in queue: {queue_type.qsize()}")
        try:
            if queue_type == customer_queues[2]:
                queue_type.put((service_time, customer_id, service_time), timeout=1)
            else:
                queue_type.put((service_time, customer_id), timeout=1)
        except queue.Full:
            print("Queue is FULL.")
        customer_id += 1
        time.sleep(random.uniform(0.5, 2))

def teller_service_fcfs(teller_id):
    while not stop_event.is_set():
        try:
            service_time, customer_id = customer_queues[1].get(timeout=1)
            start_time = time.time()
            with lock:
                if customer_id not in responded:
                    response_time = start_time - arrival_times[customer_id]
                    fcfs_response_times.append(response_time)
                    responded.append(customer_id)
            print(f"Customer {customer_id} is in Teller {teller_id} at {timeConverter(start_time)}")
            time.sleep(service_time)
            end_time = time.time()
            with lock:
                completion_times[customer_id] = end_time
                turnaround_time = end_time - arrival_times[customer_id]
                fcfs_turnaround_times.append(turnaround_time)
                waiting_time = (end_time - arrival_times[customer_id]) - service_times[customer_id]
                fcfs_waiting_times.append(waiting_time)
            print(f"Customer {customer_id} leaves the Teller {teller_id} at {timeConverter(end_time)}")
        except queue.Empty:
            continue

def teller_service_sjf_preemptive(teller_id):
    while not stop_event.is_set():
        try:
            with lock:
                sorted_customers = sorted(list(customer_queues[2].queue), key=lambda x: x[0])
                customer_queues[2].queue.clear()
                for customer in sorted_customers:
                    customer_queues[2].put_nowait(customer)

            service_time, customer_id, remaining_time = customer_queues[2].get(timeout=1)
            start_time = time.time()
            with lock:
                if customer_id not in responded:
                    response_time = start_time - arrival_times[customer_id]
                    sjf_preemptive_response_times.append(response_time)
                    responded.append(customer_id)
            print(f"Customer {customer_id} is in Teller {teller_id} at {timeConverter(start_time)}")
            if remaining_time <= QUANTUM_TIME:
                time.sleep(remaining_time)
                end_time = time.time()
                with lock:
                    completion_times[customer_id] = end_time
                    turnaround_time = end_time - arrival_times[customer_id]
                    sjf_preemptive_turnaround_times.append(turnaround_time)
                    waiting_time = (end_time - arrival_times[customer_id]) - service_times[customer_id]
                    sjf_preemptive_waiting_times.append(waiting_time)
                print(f"Customer {customer_id} leaves the Teller {teller_id} at {timeConverter(end_time)}")
            else:
                time.sleep(QUANTUM_TIME)
                mid_time = time.time()
                remaining_time -= QUANTUM_TIME
                with lock:
                    print(f"Customer {customer_id} leaves the Teller {teller_id} at {timeConverter(mid_time)}")
                    customer_queues[2].put((service_time, customer_id, remaining_time))
        except queue.Empty:
            continue

def teller_service_rr(teller_id):
    while not stop_event.is_set():
        try:
            service_time, customer_id = customer_queues[3].get(timeout=1)
            start_time = time.time()
            with lock:
                if customer_id not in responded:
                    response_time = start_time - arrival_times[customer_id]
                    rr_response_times.append(response_time)
                    responded.append(customer_id)
            print(f"Customer {customer_id} is in Teller {teller_id} for a quantum of {QUANTUM_TIME} at {timeConverter(start_time)}")
            if service_time <= QUANTUM_TIME:
                time.sleep(service_time)
                end_time = time.time()
                with lock:
                    completion_times[customer_id] = end_time
                    turnaround_time = end_time - arrival_times[customer_id]
                    rr_turnaround_times.append(turnaround_time)
                    waiting_time = (end_time - arrival_times[customer_id]) - service_times[customer_id]
                    rr_waiting_times.append(waiting_time)
                print(f"Customer {customer_id} leaves the Teller {teller_id} at {timeConverter(end_time)}")
            else:
                time.sleep(QUANTUM_TIME)
                mid_time = time.time()
                remaining_time = service_time - QUANTUM_TIME
                with lock:
                    print(f"Customer {customer_id} leaves the Teller {teller_id} at {timeConverter(mid_time)}")
                    customer_queues[3].put((remaining_time, customer_id))
        except queue.Empty:
            continue

def start_simulation(choice):
    if choice == 1:
        service_function = teller_service_fcfs
        queue_type = customer_queues[1]
        description = "FCFS"
    elif choice == 2:
        service_function = teller_service_sjf_preemptive
        queue_type = customer_queues[2]
        description = "SJF Preemptive"
    elif choice == 3:
        service_function = teller_service_rr
        queue_type = customer_queues[3]
        description = "Round Robin"
    empty_queue(queue_type)
    customer_id = 1
    try:
        tellers = start_tellers(service_function)
        while True:
            if customer_id > CUSTOMER_LIMIT:
                raise LimitCross('Customer Limit reached.')
            customer_arrival(queue_type)
            customer_id += 1
            time.sleep(random.uniform(0.5, 2))
    except (KeyboardInterrupt, LimitCross) as e:
        print(f"Simulation stopped. {e}")
        stop_event.set()
    finally:
        for t in tellers:
            t.join()
        stop_event.clear()
        responded.clear()
        return calculate_stats(description)

def start_tellers(service_function):
    tellers = []
    for i in range(1, NUM_TELLERS + 1):
        t = threading.Thread(target=service_function, args=(i,))
        t.start()
        tellers.append(t)
    return tellers

def calculate_stats(description):
    if description == 'FCFS':
        turnaround_times = fcfs_turnaround_times
        waiting_times = fcfs_waiting_times
        response_times = fcfs_response_times
    elif description == 'SJF Preemptive':
        turnaround_times = sjf_preemptive_turnaround_times
        waiting_times = sjf_preemptive_waiting_times
        response_times = sjf_preemptive_response_times
    elif description == 'Round Robin':
        turnaround_times = rr_turnaround_times
        waiting_times = rr_waiting_times
        response_times = rr_response_times
    
    if not turnaround_times:  # Check if the list is empty
        avg_turnaround_time = 0
    else:
        avg_turnaround_time = sum(turnaround_times) / len(turnaround_times)
        
    if not waiting_times:  # Check if the list is empty
        avg_waiting_time = 0
    else:
        avg_waiting_time = sum(waiting_times) / len(waiting_times)
        
    if not response_times:  # Check if the list is empty
        avg_response_time = 0
    else:
        avg_response_time = sum(response_times) / len(response_times)

    print(f"\nStatistics for {description}:")
    print(f"Average Turnaround Time: {avg_turnaround_time:.4f} seconds")
    print(f"Average Waiting Time: {avg_waiting_time:.4f} seconds")
    print(f"Average Response Time: {avg_response_time:.4f} seconds")

    return avg_turnaround_time, avg_waiting_time, avg_response_time


def plot_results(fcfs, sjf_preemptive, rr):
    algorithms = ['FCFS', 'SJF Preemptive', 'Round Robin']
    turnaround_times = [fcfs[0], sjf_preemptive[0], rr[0]]
    waiting_times = [fcfs[1], sjf_preemptive[1], rr[1]]
    response_times = [fcfs[2], sjf_preemptive[2], rr[2]]

    x = range(len(algorithms))

    plt.figure(figsize=(10, 6))
    plt.bar(x, turnaround_times, width=0.2, label='Turnaround Time', align='center')
    plt.bar([p + 0.2 for p in x], waiting_times, width=0.2, label='Waiting Time', align='center')
    plt.bar([p + 0.4 for p in x], response_times, width=0.2, label='Response Time', align='center')

    plt.xlabel('Scheduling Algorithms')
    plt.ylabel('Time (seconds)')
    plt.title('Comparison of Scheduling Algorithms')
    plt.xticks([p + 0.2 for p in x], algorithms)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    print("Select the scheduling algorithm you want to use:")
    print("1: FCFS")
    print("2: SJF Preemptive")
    print("3: Round Robin")
    choice = int(input())

    fcfs_stats = start_simulation(1)
    sjf_preemptive_stats = start_simulation(2)
    rr_stats = start_simulation(3)

    plot_results(fcfs_stats, sjf_preemptive_stats, rr_stats)
