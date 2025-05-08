import sys
import os
import threading

FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb'))
sys.path.insert(0, grpc_path)

import common_pb2 as common  # noqa
import common_pb2_grpc as common_grpc  # noqa
import books_database_pb2 as books_database  # noqa
import books_database_pb2_grpc as books_database_grpc  # noqa
from concurrent import futures  # noqa
import docker  # noqa
import grpc  # noqa


class BooksDatabase(books_database_grpc.BooksDatabaseServicer, common_grpc.TransactionService):
    def __init__(self):
        self.store = {
            '1984 by George Orwell': 100,
            'A Brave New World by Aldous Huxley': 100,
            'To Kill a Mockingbird by Harper Lee': 100,
            'The Great Gatsby by F. Scott Fitzgerald': 100,
        }
        self.temp_updates = {}
        # Dictionary of locks for each book title
        self.locks = {}
        # Global lock for creating new book locks
        self.global_lock = threading.Lock()

    def _get_lock_for_book(self, title):
        with self.global_lock:
            if title not in self.locks:
                self.locks[title] = threading.Lock()
            return self.locks[title]

    def Read(self, request, context):
        # Reading doesn't modify data, so no lock needed
        stock = self.store.get(request.title, 0)
        return books_database.ReadResponse(stock=stock)

    def Write(self, request, context):
        lock = self._get_lock_for_book(request.title)
        with lock:
            self.store[request.title] = request.new_stock
            return books_database.WriteResponse(success=True)

    def DecrementStock(self, request, context):
        lock = self._get_lock_for_book(request.title)
        with lock:
            stock = self.store.get(request.title, 0)
            if stock < request.amount or request.amount < 0:
                return books_database.WriteResponse(success=False)
            self.store[request.title] = stock - request.amount
            return books_database.WriteResponse(success=True)

    def IncrementStock(self, request, context):
        lock = self._get_lock_for_book(request.title)
        with lock:
            stock = self.store.get(request.title, 0)
            if request.amount < 0:
                return books_database.WriteResponse(success=False)
            self.store[request.title] = stock + request.amount
            return books_database.WriteResponse(success=True)

    def Prepare(self, request, context):
        lock = self._get_lock_for_book(request.title)
        with lock:
            stock = self.store.get(request.title, 0)
            if stock < request.amount or request.amount < 0:
                return common.PrepareResponse(ready=False)
            self.temp_updates[request.order_id] = request
            return common.PrepareResponse(ready=True)

    def Commit(self, request, context):
        prepared_request = self.temp_updates.pop(request.order_id, None)
        if prepared_request is not None:
            lock = self._get_lock_for_book(request.title)
            with lock:
                response = self.DecrementStock(prepared_request, context)
                print(
                    f"Commit successful for order {request.order_id}, title: {request.title}, updated stock: {self.store.get(request.title, 0)}")
                return common.CommitResponse(success=response.success)
        else:
            return common.CommitResponse(success=False)

    def Abort(self, request, context):
        self.temp_updates.pop(request.order_id, None)
        return common.AbortResponse(aborted=True)


class PrimaryReplica(BooksDatabase):
    def __init__(self, backup_stubs: list[books_database_grpc.BooksDatabaseStub]):
        super().__init__()
        self.backups = backup_stubs

    def Write(self, request, context):
        self.store[request.title] = request.new_stock

        for backup in self.backups:
            try:
                backup.Write(request)
            except Exception as e:
                print(
                    f"Failed to replicate to backup: {e}, title: {request.title}, value: {request.new_stock}")

        return books_database.WriteResponse(success=True)

    def DecrementStock(self, request, context):
        stock = self.store.get(request.title, 0)
        if stock < request.amount or request.amount < 0:
            return books_database.WriteResponse(success=False)
        self.store[request.title] = stock - request.amount

        for backup in self.backups:
            try:
                backup.Write(books_database.WriteRequest(
                    title=request.title, new_stock=self.store[request.title]))
            except Exception as e:
                print(
                    f"Failed to replicate to backup: {e}, title: {request.title}, value: {request.new_stock}")

        return books_database.WriteResponse(success=True)

    def IncrementStock(self, request, context):
        stock = self.store.get(request.title, 0)
        if request.amount < 0:
            return books_database.WriteResponse(success=False)
        self.store[request.title] = stock + request.amount

        for backup in self.backups:
            try:
                backup.Write(books_database.WriteRequest(
                    title=request.title, new_stock=self.store[request.title]))
            except Exception as e:
                print(
                    f"Failed to replicate to backup: {e}, title: {request.title}, value: {request.new_stock}")
        return books_database.WriteResponse(success=True)


def get_backup_ids():
    docker_client = docker.from_env()

    replica_container_ids = []
    for container_instance in docker_client.containers.list(all=True):
        if container_instance.labels.get('com.docker.compose.service') == 'books_database':
            replica_container_ids.append(container_instance.short_id)

    return replica_container_ids


def serve():
    is_primary = os.getenv('IS_PRIMARY', '').upper() == 'TRUE'

    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())

    if is_primary:
        backup_stubs = []
        for backup_id in get_backup_ids():
            channel = grpc.insecure_channel(f'{backup_id}:50051')
            stub = books_database_grpc.BooksDatabaseStub(channel)
            backup_stubs.append(stub)
        service = PrimaryReplica(backup_stubs)
    else:
        service = BooksDatabase()

    books_database_grpc.add_BooksDatabaseServicer_to_server(service, server)
    common_grpc.add_TransactionServiceServicer_to_server(service, server)

    # Listen on port 50051
    port = "50051"
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print("Server started. Listening on port 50051.")
    # Keep thread alive
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
