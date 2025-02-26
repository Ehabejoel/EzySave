import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import os
import io
from PIL import Image
from urllib.parse import urljoin, urlparse
import threading
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class WebImageDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Image Downloader")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        self.images = []
        self.download_format = tk.StringVar(value="jpg")
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.use_selenium = tk.BooleanVar(value=False)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0"
        ]
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # URL input area
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(url_frame, text="Website URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.fetch_btn = ttk.Button(url_frame, text="Fetch Images", command=self.start_fetch_thread)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding=10)
        options_frame.pack(fill=tk.X, pady=10)
        
        # Format selection
        format_frame = ttk.Frame(options_frame)
        format_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(format_frame, text="Download Format:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="JPG", variable=self.download_format, value="jpg").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="PNG", variable=self.download_format, value="png").pack(side=tk.LEFT, padx=5)
        
        # Download path
        path_frame = ttk.Frame(options_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="Download Path:").pack(side=tk.LEFT, padx=5)
        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.insert(0, self.download_path)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(path_frame, text="Browse", command=self.select_path).pack(side=tk.LEFT, padx=5)
        
        # Advanced options
        advanced_frame = ttk.Frame(options_frame)
        advanced_frame.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(advanced_frame, text="Use Selenium (for JavaScript-heavy sites)", variable=self.use_selenium).pack(side=tk.LEFT, padx=5)
        
        # Image list area
        list_frame = ttk.LabelFrame(main_frame, text="Images Found", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create a frame with scrollbar for the listbox
        list_scroll_frame = ttk.Frame(list_frame)
        list_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.image_listbox = tk.Listbox(list_scroll_frame, selectmode=tk.EXTENDED)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_scroll_frame, orient=tk.VERTICAL, command=self.image_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_listbox.config(yscrollcommand=scrollbar.set)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
        
        ttk.Button(button_frame, text="Download Selected", command=self.download_selected).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Download All", command=self.download_all).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Select All", command=self.select_all).pack(side=tk.RIGHT, padx=5)
    
    def select_path(self):
        path = filedialog.askdirectory()
        if path:
            self.download_path = path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
    
    def select_all(self):
        self.image_listbox.select_set(0, tk.END)
    
    def start_fetch_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL")
            return
        
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
        
        self.fetch_btn.config(state=tk.DISABLED)
        self.status_var.set("Fetching images...")
        self.progress_bar.start()
        
        thread = threading.Thread(target=self.fetch_images)
        thread.daemon = True
        thread.start()
    
    def show_error(self, message):
        """Helper method to show error messages"""
        messagebox.showerror("Error", message)

    def test_connection(self, url):
        """Test connection to the given URL"""
        try:
            # Try to connect to the host first
            parsed_url = urlparse(url)
            test_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = requests.head(test_url, headers=headers, timeout=5)
            return True
        except:
            return False

    def fetch_images(self):
        try:
            url = self.url_entry.get()
            
            # Test connection first
            if not self.test_connection(url):
                raise ConnectionError("Unable to connect to the website. Please check your internet connection or the URL.")
            
            if self.is_valid_image_url(url):
                self.images = [url]
            else:
                if self.use_selenium.get():
                    self.images = self.fetch_with_selenium(url)
                else:
                    self.images = self.fetch_with_requests(url)
            
            self.root.after(0, self.update_image_list)
        except ConnectionError as e:
            error_message = str(e)
            self.root.after(0, lambda: self.show_error(error_message))
        except Exception as e:
            error_message = f"Failed to fetch images: {str(e)}"
            self.root.after(0, lambda: self.show_error(error_message))
        finally:
            self.root.after(0, self.stop_progress)

    def fetch_with_requests(self, url):
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': url,
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            images = []
            
            # Find all image tags
            for img in soup.find_all('img'):
                img_url = img.get('src')
                if img_url:
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(url, img_url)
                    if self.is_valid_image_url(absolute_url):
                        images.append(absolute_url)
            
            # Find images in CSS background
            for tag in soup.find_all(['div', 'span', 'a', 'section']):
                style = tag.get('style')
                if style and 'background-image' in style:
                    # Extract URL from background-image: url('...')
                    start = style.find('url(')
                    if start != -1:
                        start += 4
                        end = style.find(')', start)
                        if end != -1:
                            img_url = style[start:end].strip('\'"')
                            absolute_url = urljoin(url, img_url)
                            if self.is_valid_image_url(absolute_url):
                                images.append(absolute_url)
            
            return images
        except requests.RequestException as e:
            if "ProxyError" in str(e) or "ConnectionError" in str(e):
                raise ConnectionError("Unable to connect to the website. Please check your internet connection.")
            raise
    
    def fetch_with_selenium(self, url):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            driver.get(url)
            # Wait for dynamic content to load
            time.sleep(3)
            
            # Scroll to capture lazy-loaded images
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Get page content after JavaScript execution
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            images = []
            
            # Find all image tags
            for img in soup.find_all('img'):
                img_url = img.get('src')
                if img_url:
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(url, img_url)
                    if self.is_valid_image_url(absolute_url):
                        images.append(absolute_url)
            
            # Extract CSS background images
            script = """
            var results = [];
            var allElements = document.querySelectorAll('*');
            for (var i = 0; i < allElements.length; i++) {
                var style = window.getComputedStyle(allElements[i]);
                var backgroundImage = style.backgroundImage;
                if (backgroundImage && backgroundImage !== 'none') {
                    var url = backgroundImage.slice(4, -1).replace(/["']/g, "");
                    results.push(url);
                }
            }
            return results;
            """
            background_images = driver.execute_script(script)
            
            for img_url in background_images:
                absolute_url = urljoin(url, img_url)
                if self.is_valid_image_url(absolute_url):
                    images.append(absolute_url)
            
            return images
        finally:
            driver.quit()
    
    def is_valid_image_url(self, url):
        # Update the function to handle more image formats
        parsed = urlparse(url)
        path = parsed.path.lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.ico']
        return any(path.endswith(ext) for ext in valid_extensions)
    
    def update_image_list(self):
        self.image_listbox.delete(0, tk.END)
        
        for img_url in self.images:
            self.image_listbox.insert(tk.END, img_url)
        
        self.status_var.set(f"Found {len(self.images)} images")
    
    def stop_progress(self):
        self.progress_bar.stop()
        self.fetch_btn.config(state=tk.NORMAL)
    
    def download_selected(self):
        selected_indices = self.image_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "No images selected")
            return
        
        selected_urls = [self.images[i] for i in selected_indices]
        self.start_download_thread(selected_urls)
    
    def download_all(self):
        if not self.images:
            messagebox.showinfo("Info", "No images to download")
            return
        
        self.start_download_thread(self.images)
    
    def start_download_thread(self, urls):
        self.status_var.set(f"Downloading {len(urls)} images...")
        self.progress_bar.start()
        
        thread = threading.Thread(target=self.download_images, args=(urls,))
        thread.daemon = True
        thread.start()
    
    def download_images(self, urls):
        download_format = self.download_format.get()
        download_path = self.path_entry.get()
        
        if not os.path.exists(download_path):
            try:
                os.makedirs(download_path)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to create download directory: {str(e)}"))
                self.root.after(0, self.stop_progress)
                return
        
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls):
            try:
                # Update progress
                self.root.after(0, lambda i=i, total=len(urls): 
                    self.status_var.set(f"Downloading image {i+1}/{total}..."))
                
                # Random delay to avoid being blocked
                time.sleep(random.uniform(0.5, 1.5))
                
                # Handle SVG files differently
                if url.lower().endswith('.svg'):
                    # For SVG files, just save them directly without processing
                    headers = {'User-Agent': random.choice(self.user_agents)}
                    response = requests.get(url, headers=headers, timeout=15)
                    response.raise_for_status()
                    
                    # Save SVG file with original format regardless of selected format
                    original_filename = os.path.basename(urlparse(url).path)
                    filename_without_ext = os.path.splitext(original_filename)[0]
                    safe_filename = ''.join(c for c in filename_without_ext if c.isalnum() or c in '._- ')
                    if not safe_filename:
                        safe_filename = f"image_{i+1}"
                    
                    save_path = os.path.join(download_path, f"{safe_filename}.svg")
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    
                else:
                    # Handle raster images
                    headers = {'User-Agent': random.choice(self.user_agents)}
                    response = requests.get(url, headers=headers, timeout=15, stream=True)
                    response.raise_for_status()
                    
                    # Get the image content
                    image_content = response.content
                    
                    # Open the image with PIL
                    img = Image.open(io.BytesIO(image_content))
                    
                    # Convert image to RGB, handling different modes
                    if img.mode in ('P', 'PA'):
                        # Convert palette images to RGBA first if they have transparency
                        if 'transparency' in img.info:
                            img = img.convert('RGBA')
                        else:
                            img = img.convert('RGB')
                    
                    if img.mode == 'RGBA':
                        # Create a white background for transparent images
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Get original filename without extension
                    original_filename = os.path.basename(urlparse(url).path)
                    filename_without_ext = os.path.splitext(original_filename)[0]
                    
                    # Create a safe filename
                    safe_filename = ''.join(c for c in filename_without_ext if c.isalnum() or c in '._- ')
                    if not safe_filename:
                        safe_filename = f"image_{i+1}"
                    
                    # Save with the desired format
                    save_path = os.path.join(download_path, f"{safe_filename}.{download_format}")
                    img.save(save_path, quality=95 if download_format.lower() == 'jpg' else None)
                
                successful += 1
                
            except Exception as e:
                failed += 1
                print(f"Failed to download {url}: {str(e)}")
        
        message = f"Download complete. {successful} images downloaded successfully."
        if failed > 0:
            message += f" {failed} images failed."
        
        final_message = message
        self.root.after(0, lambda: self.status_var.set(final_message))
        self.root.after(0, lambda msg=final_message: messagebox.showinfo("Download Complete", msg))
        self.root.after(0, self.stop_progress)

if __name__ == "__main__":
    root = tk.Tk()
    app = WebImageDownloader(root)
    root.mainloop()