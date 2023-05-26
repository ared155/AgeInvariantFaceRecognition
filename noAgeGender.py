import tkinter as tk
import cv2
from PIL import Image, ImageTk
import numpy as np
from tkinter.filedialog import askopenfilename
import shutil
import time
import os
import sys
from matplotlib import pyplot
from numpy import asarray
from scipy.spatial.distance import cosine
from mtcnn.mtcnn import MTCNN
from keras_vggface.vggface import VGGFace
from keras_vggface.utils import preprocess_input

global fileName1,fileName2

class App:
    def __init__(self, window, window_title, video_source):
        self.window = window
        self.window.title(window_title)

        # Open the video source
        self.cap = cv2.VideoCapture(video_source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Create a canvas that can fit the video source
        self.canvas = tk.Canvas(window, width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.canvas.pack()
        
        # Use PIL (Pillow) to convert the OpenCV image to a Tkinter image
        self.photo = None
        self.update()
        
        dirPath = "testpicture"
        fileList = os.listdir(dirPath)
        for fileName in fileList:
            os.remove(dirPath + "/" + fileName)


        def openphoto():
            global fileName1
            fileName1 = askopenfilename(title='Select image for analysis ', filetypes=[('image files', '.jpg')])
            dst = "testpicture"
            print(fileName1)
            print (os.path.split(fileName1)[-1])
            shutil.copy(fileName1, dst)
            load1 = Image.open(fileName1)
            im1=load1.resize((300,300), Image.ANTIALIAS)
            render = ImageTk.PhotoImage(im1)
            img = tk.Label(image=render, height="300", width="300")
            img.image = render
            img.place(x=500, y=75)

        def openphoto2():
            global fileName2
            fileName2 = askopenfilename(initialdir='', title='Select image for analysis ',filetypes=[('image files', '.jpg')])
            dst = "testpicture"
            print(fileName2)
            print (os.path.split(fileName2)[-1])
            shutil.copy(fileName2, dst)
            load2 = Image.open(fileName2)
            im2=load2.resize((300,300), Image.ANTIALIAS)
            render = ImageTk.PhotoImage(im2)
            img1 = tk.Label(image=render, height="300", width="300")
            img1.image = render
            img1.place(x=500, y=400)

        detector = MTCNN()
        model = VGGFace(model='resnet50', include_top=False, input_shape=(224, 224, 3), pooling='avg')

        def extract_face_live(filename,detector=detector,required_size=(224, 224)):
            pixels = pyplot.imread(filename)
            # detect faces in the image
            results = detector.detect_faces(pixels)
            # extract the bounding box from the first face
            x1, y1, width, height = results[0]['box']
            x2, y2 = x1 + width, y1 + height
            face = pixels[y1:y2, x1:x2]
            image = Image.fromarray(face)
            image = image.resize(required_size)
            face_array = asarray(image)
            return face_array
        
        def get_embeddings_live(face, model=model):
            samples = asarray(face, 'float32')
            samples = preprocess_input(samples, version=2)
            samples = samples[np.newaxis,:]
            yhat = model.predict(samples)
            return yhat
        
        def open_camera():
            flag = False
            start_time = time.time()
            video_capture = cv2.VideoCapture(0)
            ID_face = extract_face_live(fileName1,detector)
            ID_embedding=get_embeddings_live(ID_face,model)
            while True:
                _, frame = video_capture.read()
                try:
                    result = detector.detect_faces(frame)
                    if result != []:
                        for _ in result:
                            x1, y1, width, height = result[0]['box']
                            x2, y2 = x1 + width, y1 + height
                            # extract the face
                            face = frame[y1:y2, x1:x2]
                            # resize pixels to the model size
                            subject_face = Image.fromarray(face)
                            required_size=(224, 224)
                            subject_face = subject_face.resize(required_size)
                            sample = asarray(subject_face, 'float32')
                            sample = preprocess_input(sample, version=2)
                            subject_embeddings = get_embeddings_live(subject_face)
                            score = cosine(ID_embedding, subject_embeddings)
                            thresh = 0.5
                            if score <= thresh:
                                print('>face is a Match (%.3f <= %.3f)' % (score, thresh))
                                r = tk.Label(text="STATUS: FACE MATCHED", background="white", fg="black", font=("", 15))
                                r.place(x=1000,y=400)
                                flag=True
                            else:
                                print('>face is NOT a Match (%.3f > %.3f)' % (score, thresh))
                except ValueError:
                    pass
                
                cv2.imshow('Video', frame)
                temp_time = time.time()
                print("TIME : ", temp_time-start_time)
                if (cv2.waitKey(1) & 0xFF == ord('q')) or flag==True or (temp_time-start_time)>10:
                    break
            video_capture.release()
            if flag==False:
                r = tk.Label(text='STATUS: FACE NOT MATCHED....', background="white", fg="red", font=("", 15))
                r.place(x=1000,y=400)
            cv2.destroyAllWindows()

        def main():
            def extract_face(filename, required_size=(224, 224)):
                # load image from file
                pixels = pyplot.imread(filename)
                # create the detector, using default weights
                detector = MTCNN()
                # detect faces in the image
                results = detector.detect_faces(pixels)
                # extract the bounding box from the first face
                x1, y1, width, height = results[0]['box']
                x2, y2 = x1 + width, y1 + height
                print("FACE DETECTED.....")                                
                face = pixels[y1:y2, x1:x2]
                image = Image.fromarray(face)
                image = image.resize(required_size)
                face_array = asarray(image)
                return face_array

            # extract faces and calculate face embeddings for a list of photo files
            def get_embeddings(filenames):
                count=0
                faces = [extract_face(f) for f in filenames]
                samples = asarray(faces, 'float32')
                samples = preprocess_input(samples, version=2)
                model = VGGFace(model='resnet50', include_top=False, input_shape=(224, 224, 3), pooling='avg')
                yhat = model.predict(samples)
                return yhat
            
            def is_match(known_embedding, candidate_embedding, thresh=0.5):
                score = cosine(known_embedding, candidate_embedding)
                if score <= thresh:
                    print('>face is a Match (%.3f <= %.3f)' % (score, thresh))
                    r = tk.Label(text="Status: Face Matched", background="white", fg="Brown", font=("", 15))
                    r.place(x=1000,y=400)

                    button = tk.Button(text="Exit", command=exit,height=2,width=10,background="#3b1d7d", fg="black", font=("", 15),activebackground="red")
                    button.place(x=1000,y=600)
                else:
                    print('>face is NOT a Match (%.3f > %.3f)' % (score, thresh))
                    r = tk.Label(text='STATUS: FACE NOT MATCHED', background="white", fg="black", font=("", 15))
                    r.place(x=975,y=400)
                    button = tk.Button(text="Exit", command=exit,height=2,width=10,background="#3b1d7d", fg="black", font=("", 15))
                    button.place(x=1000,y=600)

            global fileName1,fileName2      
            filenames = [fileName1,fileName2]
            embeddings = get_embeddings(filenames)
            is_match(embeddings[0], embeddings[1])

        buttonr = tk.Button(text="WEB CAMERA", command = open_camera, height=1,width=15,fg="black",bg="#E8F6EF",font=("times",15,"bold"))
        buttonr.place(x=100,y=350)

        buttonA = tk.Button(text="ANALYSE", command = main,height=1,width=15,fg="black",bg="#E8F6EF",font=("times",15,"bold"))
        buttonA.place(x=1000,y=200)

        buttono = tk.Button(text="OLD PHOTO", command = openphoto,height=1,width=15,fg="black",bg="#E8F6EF",font=("times",15,"bold"))
        buttono.place(x=100,y=200)

        buttonr = tk.Button(text="RECENT PHOTO", command = openphoto2,height=1,width=15,fg="black",bg="#E8F6EF",font=("times",15,"bold"))
        buttonr.place(x=100,y=500)

        window.mainloop()
        self.window.mainloop()
    
    def update(self):
        ret, frame = self.cap.read()
        if ret:
            self.photo = ImageTk.PhotoImage(image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tk.NW) 
        self.window.after(15, self.update)

App(tk.Tk(), "Face Age Invariance Recognition", "video.mp4")
