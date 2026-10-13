import hashlib
from flask import Flask, request, redirect, jsonify, render_template_string

app = Flask(__name__)
url_db = {}  # { short_code: { url, clicks } }


def generate_code(url):
    return hashlib.md5(url.encode()).hexdigest()[:6]


INDEX_TEMPLATE = """
<!DOCTYPE html><html><body>
<h2>URL Shortener</h2>
<form method="POST" action="/shorten">
  <input name="url" placeholder="Enter long URL" style="width:300px">
  <button type="submit">Shorten</button>
</form>
{% if short_url %}<p>Short URL: <a href="{{ short_url }}">{{ short_url }}</a></p>{% endif %}
<hr>
{% for code, data in links.items() %}
  <p>/{{ code }} -> {{ data.url }} ({{ data.clicks }} clicks)</p>
{% endfor %}
</body></html>
"""


@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE, short_url=None, links=url_db)


@app.route('/shorten', methods=['POST'])
def shorten():
    url = request.form.get('url', '').strip()
    if not url.startswith('http'):
        url = 'https://' + url
    code = generate_code(url)
    if code not in url_db:
        url_db[code] = {'url': url, 'clicks': 0}
    short_url = f"http://localhost:5000/{code}"
    return render_template_string(INDEX_TEMPLATE, short_url=short_url, links=url_db)


@app.route('/<code>')
def redirect_url(code):
    if code in url_db:
        url_db[code]['clicks'] += 1
        return redirect(url_db[code]['url'])
    return "Short URL not found.", 404


if __name__ == '__main__':
    app.run(debug=True)
