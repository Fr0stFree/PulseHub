from bubus import EventBus
from dependency_injector import containers, providers
from opentelemetry import trace

from common.brokers.kafka import KafkaProducer
from common.databases.redis import RedisClient
from common.grpc import GRPCServer
from common.http import HTTPServer
from common.logs import LoggerHandle
from common.metrics import MetricsExporter
from common.service import BaseService
from common.tracing import TraceExporter
from service_crawler.src.factories import new_repository, new_rpc_servicer, new_worker_manager
from service_crawler.src.settings import CrawlerServiceSettings


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration(pydantic_settings=[CrawlerServiceSettings()])

    # observability
    logger_handle = providers.Singleton(
        LoggerHandle,
        name=settings.service_name,
        is_export_enabled=settings.logging.is_export_enabled,
        exporting_endpoint=settings.logging.exporting_endpoint,
        level=settings.logging.level,
    )
    logger = logger_handle.provided.logger
    metrics_exporter = providers.Singleton(
        MetricsExporter,
        name=settings.service_name,
        endpoint=settings.metrics_exporter.otlp_endpoint,
        is_enabled=settings.metrics_exporter.enabled,
        logger=logger,
    )
    trace_exporter = providers.Singleton(
        TraceExporter,
        name=settings.service_name,
        endpoint=settings.trace_exporter.otlp_endpoint,
        is_enabled=settings.trace_exporter.enabled,
        logger=logger,
    )
    tracer = providers.Singleton(trace.get_tracer, settings.service_name)
    current_span = providers.Factory(trace.get_current_span)

    # metrics
    grpc_incoming_requests_counter = providers.Singleton(
        metrics_exporter.provided.meter.create_counter.call(),
        name="service_crawler_incoming_grpc_requests_total",
        description="Total number of incoming gRPC requests",
        unit="1",
    )
    grpc_incoming_requests_latency = providers.Singleton(
        metrics_exporter.provided.meter.create_histogram.call(),
        name="service_crawler_incoming_grpc_requests_latency_seconds",
        description="Latency of incoming gRPC requests in seconds",
        unit="s",
    )
    # TODO: producer metrics

    # components
    rpc_servicer = providers.Singleton(new_rpc_servicer)
    grpc_server = providers.Singleton(
        GRPCServer,
        worker_amount=settings.grpc_server.worker_amount,
        port=settings.grpc_server.port,
        logger=logger,
    )
    http_server = providers.Singleton(
        HTTPServer,
        port=settings.http_server.port,
        logger=logger,
    )
    broker_producer = providers.Singleton(
        KafkaProducer,
        topic=settings.kafka_producer.topic,
        address=settings.kafka_producer.address,
        client_prefix=settings.service_name,
        logger=logger,
    )
    db_client = providers.Singleton(
        RedisClient,
        host=settings.redis.host,
        port=settings.redis.port,
        password=settings.redis.password,
        database=settings.redis.database,
        logger=logger,
    )
    worker_manager = providers.Singleton(new_worker_manager, concurrent_workers=settings.concurrent_workers)
    repository = providers.Singleton(new_repository)

    service = providers.Singleton(
        BaseService,
        components=providers.List(
            logger_handle,
            http_server,
            trace_exporter,
            metrics_exporter,
            grpc_server,
            db_client,
            broker_producer,
            repository,
            worker_manager,
        ),
        name=settings.service_name,
        health_check_timeout=settings.health_check_timeout,
        logger=logger,
    )
    event_bus = providers.Singleton(EventBus)
