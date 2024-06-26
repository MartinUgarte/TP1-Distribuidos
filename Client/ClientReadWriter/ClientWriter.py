import signal
from utils.Batch import Batch
from utils.DatasetHandler import DatasetWriter
from utils.QueryMessage import QueryMessage, query_result_headers, query_to_query_result


class ClientWriter():
    def __init__(self, socket, queries, query_path):
        self.socket = socket
        writers = {}
        for query in queries:
            query_result = query_to_query_result(query)
            header = query_result_headers(query_result)
            path = query_path + query + '.csv'
            dw = DatasetWriter(path, header)
            writers[query_result] = dw
        self.writers = writers

    def handle_SIGTERM(self, _signum, _frame):
        print("\n\n [ClientWriter] SIGTERM detected\n\n")
        self.socket.close()

    def start(self):
        signal.signal(signal.SIGTERM, self.handle_SIGTERM)
        while True:
            try:
                result_batch = Batch.from_socket(self.socket, QueryMessage)
                if not result_batch:
                    print("[ClientWriter] Socket disconnected")
                    break
            except OSError:
                print("[ClientWriter] Socket disconnected")
                break
            if result_batch.is_empty():
                print("[ClientWriter] Finished receiving")
                break
            self.writers[result_batch[0].msg_type].append_objects(result_batch)
        self.close()

    def close(self):
        for writer in self.writers.values():
            writer.close()