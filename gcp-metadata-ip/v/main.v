import net.http

const meta_url = 'https://metadata/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip'
const ip_url = 'https://api.ipify.org'

fn retrieve_ip(url string) ! {
	mut header := http.Header{}
	header.add_custom('Metadata-Flavor', 'Google')!
	fc := &http.FetchConfig{
		url:    url
		header: header
	}
	mut res := http.fetch(fc) or {
		println('error connecting to ${url}: ${err}')
		return err
	}
	println(res.body)
}

fn main() {
	retrieve_ip(meta_url) or { retrieve_ip(ip_url)! }
}
