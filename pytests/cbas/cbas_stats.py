import json

from cbas.cbas_base import CBASBaseTest
from sdk_client import SDKClient
import uuid


class CbasStats(CBASBaseTest):

    def setUp(self):
        super(CbasStats, self).setUp()
    
    '''
    cbas.cbas_stats.CbasStats.fetch_stats_on_cbas_node,cb_bucket_name=default,cbas_bucket_name=default_bucket,cbas_dataset_name=default_ds,items=10
    '''
    def fetch_stats_on_cbas_node(self):
        
        self.log.info("Add Json documents to default bucket")
        self.perform_doc_ops_in_all_cb_buckets(self.num_items, "create", 0, self.num_items)
        
        self.log.info("Create reference to SDK client")
        client = SDKClient(scheme="couchbase", hosts=[self.master.ip], bucket=self.cb_bucket_name,
                           password=self.master.rest_password)

        self.log.info("Insert binary data into default bucket")
        keys = ["%s" % (uuid.uuid4()) for i in range(0, self.num_items)]
        client.insert_binary_document(keys)

        self.log.info("Create connection")
        self.cbas_util.createConn(self.cb_bucket_name)

        self.log.info("Create bucket on CBAS")
        self.assertTrue(self.cbas_util.create_bucket_on_cbas(cbas_bucket_name=self.cbas_bucket_name,
                                                             cb_bucket_name=self.cb_bucket_name,
                                                             cb_server_ip=self.cb_server_ip), "bucket creation failed on cbas")

        self.log.info("Create dataset on the CBAS bucket")
        self.cbas_util.create_dataset_on_bucket(cbas_bucket_name=self.cbas_bucket_name,
                                                cbas_dataset_name=self.cbas_dataset_name)

        self.log.info("Connect to Bucket")
        self.cbas_util.connect_to_bucket(cbas_bucket_name=self.cbas_bucket_name,
                                         cb_bucket_password=self.cb_bucket_password)

        self.log.info("Fetch cbas stats")
        status, content, response = self.cbas_util.fetch_cbas_stats()
        self.assertTrue(status, "Error invoking fetch cbas stats api")
        
        self.log.info("Assert Analytics stats")
        stats_json = json.loads(content)
        self.assertTrue(stats_json['gc_count'] > 0, msg='gc_count value must be greater than 0')
        self.assertTrue(stats_json['gc_time'] > 0, msg='gc_time value must be greater than 0')
        self.assertTrue(stats_json['thread_count'] > 0, msg='thread_count value must be greater than 0')
        self.assertTrue(stats_json['heap_used'] < (1024*(10**6)), msg='heap_used value must be less than configured memory value for CBAS')
        
        #self.assertEqual(stats_json[self.cb_bucket_name + ':all:failed_at_parser_records_count'], second, msg)
        #self.assertEqual(stats_json[self.cb_bucket_name + ':all:failed_at_parser_records_count_total'], second, msg)
        #self.assertEqual(stats_json[self.cb_bucket_name + ':all:incoming_records_count'], second, msg)
        #self.assertEqual(stats_json[self.cb_bucket_name + ':all:incoming_records_count_total'], second, msg)
        
        if not self.cbas_util.validate_cbas_dataset_items_count(self.cbas_dataset_name, self.num_items):
            self.fail("No. of items in CBAS dataset do not match that in the CB bucket")
        
        self.log.info("Flush the CB bucket")
        self.cluster.bucket_flush(server=self.master, bucket=self.cb_bucket_name)
        
        self.log.info("Fetch cbas stats")
        status, content, response = self.cbas_util.fetch_cbas_stats()
        self.assertTrue(status, "Error invoking fetch cbas stats api")
        
        self.log.info("Assert Analytics stats")
        stats_json = json.loads(content)

        
