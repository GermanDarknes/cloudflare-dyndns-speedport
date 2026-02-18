import cloudflare
import flask
import ipaddress
import os
import waitress

app = flask.Flask(__name__)
@app.route('/nic/update', methods=['GET'])
def main():
    hostname = flask.request.args.get('hostname')
    zone = CLOUDFLARE_ZONE
    myip = flask.request.args.get('myip')
    cf = cloudflare.Cloudflare(api_token=CLOUDFLARE_TOKEN)

    if not hostname:
        return 'bad', 400
    if not hostname.endswith(zone):
        return 'bad', 400
    if not myip:
        return 'bad', 400

    for ip in myip.split(','):
        try:
            zones = cf.zones.list(name=zone)
            if not zones.result:
                return 'bad', 404

            zone_id = zones.result[0].id

            ip = ipaddress.ip_address(ip)

            record_type = 'A'
            if ip.version == 6:
                record_type = 'AAAA'

            dns_records = cf.dns.records.list(zone_id=zone_id, name=hostname, match='all', type=record_type)

            if not dns_records.result:
                return 'bad', 404

            dns_record = dns_records.result[0]
            if dns_record.content != str(ip):
                cf.dns.records.edit(zone_id=zone_id, dns_record_id=dns_record.id, name=dns_record.name, type=record_type, content=str(ip), ttl=dns_record.ttl, proxied=dns_record.proxied)
        except (cloudflare.APIConnectionError, cloudflare.APIStatusError, Exception) as e:
            return 'bad', 500

    return 'good', 200

if __name__ == '__main__':
    CLOUDFLARE_ZONE = os.environ.get('CLOUDFLARE_ZONE')
    CLOUDFLARE_TOKEN = os.environ.get('CLOUDFLARE_TOKEN')
    waitress.serve(app, host='0.0.0.0', port=80)
