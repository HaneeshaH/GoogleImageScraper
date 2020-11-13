from selenium import webdriver
from bs4 import BeautifulSoup as bs
import random
import os
from flask import Flask, render_template, request, send_from_directory
import urllib
import time

IMG_FOLDER = os.path.join('static', 'images')

app = Flask(__name__)
app.config['IMG_FOLDER'] = IMG_FOLDER


class Scraper:
    def __init__(self):
        self.init_count = 0
        self.driver = webdriver.Chrome()

    def get_url(self, search_string=None):  # Creating url with search keyword
        search_string = search_string.split()
        search_string = '+'.join(search_string)
        url = "https://www.google.co.in/search?q=" + search_string + "&source=lnms&tbm=isch"
        return url

    def html_parsing(self, url=None):  # Parsing the webpage with beautiful soup
        self.driver.get(url)
        self.driver.maximize_window()
        page = self.driver.page_source
        html = bs(page, "html.parser")
        return html

    def scroll_down_parsing(self, url=None):  # To scroll down web page if user requests more than 50 images
        scroll_height = .1
        while scroll_height < 9.9:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scroll_height)
            scroll_height += .03
            time.sleep(0.2)
        page = self.driver.page_source
        scrolled_html = bs(page, "html.parser")
        return scrolled_html

    def clean_cache(self, directory=None):  # Cleaning the images folder before performing new request
        clean_path = directory
        # only proceed if directory is not empty
        if os.listdir(clean_path) != list():
            # iterate over the files and remove each file
            files = os.listdir(clean_path)
            for fileName in files:
                # print("Removing:", fileName)
                os.remove(os.path.join(clean_path, fileName))
        # print("Folder cleaned!")

    def save_images(self, image_boxes=None, image_count=None):  # saving images to local disk
        for i in image_boxes:
            img_link = i.get("data-src" or "src")
            if self.init_count < image_count:
                if img_link is not None:
                    print(img_link)
                    img_name = random.randrange(1, 500)
                    file_name = str(img_name) + ".jpg"
                    urllib.request.urlretrieve(img_link, os.path.join(app.config['IMG_FOLDER'], file_name))
                    self.init_count += 1


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")


@app.route("/searchImages", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        try:
            search_string = request.form['keyword']
            print("Search-term:", search_string)
            obj = Scraper()
            url = obj.get_url(search_string)
            # print("search-url:", url)

            html = obj.html_parsing(url)
            image_boxes = html.find_all("img", {"class": "rg_i Q4LuWd"})
            # print("Image-count:", len(image_boxes))

            image_count = int(request.form['count'])

            if image_count <= len(image_boxes):  # No scroll down
                obj.clean_cache(directory=app.config['IMG_FOLDER'])
                obj.save_images(image_boxes, image_count)
            else:  # scroll down and parse web page
                obj.clean_cache(directory=app.config['IMG_FOLDER'])
                scrolled_html = obj.scroll_down_parsing(url)
                image_boxes = html.find_all("img", {"class": "rg_i Q4LuWd"})
                print("Image-count:", len(image_boxes))
                obj.save_images(image_boxes, image_count)

            list_of_jpg_files = os.listdir(app.config['IMG_FOLDER'])  # getting saved images to a list
            '''for filename in list_of_jpg_files:
                  print(filename)'''
            if len(list_of_jpg_files) > 0:
                return render_template('result.html', user_images=list_of_jpg_files)

        except Exception as e:
            print(e)
    else:
        return render_template("home.html")


@app.route('/showImages/<filename>')  # route to show the review comments in a web UI
def showImages(filename):
    return send_from_directory(app.config['IMG_FOLDER'], filename)


if __name__ == "__main__":
    app.run(port=7000,debug=True)
