from confluent_kafka.admin import AdminClient, ConfigResource

def get_kafka_admin_client(cluster_address):
    return AdminClient({'bootstrap.servers': cluster_address})
