from flask_restful import Resource
import base64
import random
import string
from flask import redirect, make_response, request
from tabulate import tabulate
from models.transform import TransformModel, VisitorModel


class Transform(Resource):

    def post(self, long_url_name):
        decoded_long_url = base64.urlsafe_b64decode(long_url_name).decode('UTF-8')

        mapping = TransformModel.find_by_long_url(decoded_long_url)

        if not mapping:
            mapping = TransformModel(long_url=decoded_long_url, short_url=self.random_func(), visit_times=0)
        mapping.save_to_db()

        return mapping.short_url


    def random_func(self):
        ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 5))
        while self.check_duplication(ran_str):
            ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 5))
        return ran_str


    def check_duplication(self, ran_str):
        return TransformModel.find_by_short_url(ran_str)

class TransformBack(Resource):

    def get(self, short_url_name):
        print(request.headers)
        print('\n---------------------------------------------\n')
        # For hacking
        mapping_visitors = VisitorModel(short_url = short_url_name)
        header_recorded = ['accept_encodings', 'accept_languages', 'base_url', 'host', 'path', 'remote_addr', 'server', 'user_agent']
        for x in dir(request):
            # print('\n======================\n')
            # print(f'{x}: {getattr(request, x)}')
            if x in header_recorded:
                print(f'{x}: {getattr(request, x)}')
                setattr(mapping_visitors, x, str(getattr(request, x)))

        mapping_visitors.save_to_db()


        mapping = TransformModel.find_by_short_url(short_url_name)
        if mapping:
            mapping.visit_times += 1
            mapping.save_to_db()
            return redirect(mapping.long_url, code=302)

        return "Not exist.", 404

    def delete(self, short_url_name):
        mapping = TransformModel.find_by_short_url(short_url_name)
        mapping.delete_from_db()


class UrlReport(Resource):

    def get(self):
        mappings = TransformModel.find_all()
        data = [[mapping.short_url, mapping.long_url, mapping.visit_times] for mapping in mappings]
        table = tabulate(data, headers=["short url", "long url", "times"])
        response = make_response(table)
        response.headers['content-type'] = 'text/text'
        return response

class VisitorReport(Resource):

    def get(self, short_url_name):
        all_visitors = []
        header_recorded = ['host', 'remote_addr', 'accept_encodings', 'accept_languages', 'base_url', 'path', 'server', 'user_agent']
        visitor_mappings = VisitorModel.find_by_short_url(short_url_name)

        for mapping in visitor_mappings:
            data = [[record, getattr(mapping, record)]for record in header_recorded]
            all_visitors += (data + [[]])
            mapping = VisitorModel.find_by_short_url(short_url_name)

        table = tabulate(all_visitors)
        response = make_response(table)
        response.headers['content-type'] = 'text/text'
        return response
