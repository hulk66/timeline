
from keras.models import model_from_json
import numpy
from tensorflow import keras
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, AveragePooling2D, Flatten, Dense, Dropout
from tensorflow.keras.layers import Input, Convolution2D, ZeroPadding2D, MaxPooling2D, Flatten, Dense, Dropout, Activation
from PIL import Image, ImageOps


# Courtesy of https://github.com/serengil

class FacialExpression:
    emotions = ('angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral')

    def __init__(self) -> None:

        num_classes = 7

        self.model = Sequential()

        #1st convolution layer
        self.model.add(Conv2D(64, (5, 5), activation='relu', input_shape=(48,48,1)))
        self.model.add(MaxPooling2D(pool_size=(5,5), strides=(2, 2)))

        #2nd convolution layer
        self.model.add(Conv2D(64, (3, 3), activation='relu'))
        self.model.add(Conv2D(64, (3, 3), activation='relu'))
        self.model.add(AveragePooling2D(pool_size=(3,3), strides=(2, 2)))

        #3rd convolution layer
        self.model.add(Conv2D(128, (3, 3), activation='relu'))
        self.model.add(Conv2D(128, (3, 3), activation='relu'))
        self.model.add(AveragePooling2D(pool_size=(3,3), strides=(2, 2)))

        self.model.add(Flatten())

        #fully connected neural networks
        self.model.add(Dense(1024, activation='relu'))
        self.model.add(Dropout(0.2))
        self.model.add(Dense(1024, activation='relu'))
        self.model.add(Dropout(0.2))

        self.model.add(Dense(num_classes, activation='softmax'))
        self.model.load_weights('models/facial/facial_expression_model_weights.h5') #load weights

    def predict(self, face_image: Image): 
        face = ImageOps.grayscale(face_image).resize((48,48))
        pixels = keras.preprocessing.image.img_to_array(face)
        pixels = numpy.expand_dims(pixels, axis = 0)
        pixels /= 255
        predictions = self.model.predict(pixels) 
        max_index = numpy.argmax(predictions[0])
        emotion = self.emotions[max_index]
        return (emotion, predictions[0][max_index])


# from https://github.com/serengil/deepface/blob/master/deepface/basemodels/VGGFace.py
class AgeGender:

    def __init__(self) -> None:

        self.output_indexes = numpy.array([i for i in range(0, 101)])
        self._setup_age_model()
        self._setup_gender_model()

    def baseModel(self):
        model = Sequential()
        model.add(ZeroPadding2D((1,1),input_shape=(224,224, 3)))
        model.add(Convolution2D(64, (3, 3), activation='relu'))
        model.add(ZeroPadding2D((1,1)))
        model.add(Convolution2D(64, (3, 3), activation='relu'))
        model.add(MaxPooling2D((2,2), strides=(2,2)))

        model.add(ZeroPadding2D((1,1)))
        model.add(Convolution2D(128, (3, 3), activation='relu'))
        model.add(ZeroPadding2D((1,1)))
        model.add(Convolution2D(128, (3, 3), activation='relu'))
        model.add(MaxPooling2D((2,2), strides=(2,2)))

        model.add(ZeroPadding2D((1,1)))
        model.add(Convolution2D(256, (3, 3), activation='relu'))
        model.add(ZeroPadding2D((1,1)))
        model.add(Convolution2D(256, (3, 3), activation='relu'))
        model.add(ZeroPadding2D((1,1)))
        model.add(Convolution2D(256, (3, 3), activation='relu'))
        model.add(MaxPooling2D((2,2), strides=(2,2)))

        model.add(ZeroPadding2D((1,1)))
        model.add(Convolution2D(512, (3, 3), activation='relu'))
        model.add(ZeroPadding2D((1,1)))
        model.add(Convolution2D(512, (3, 3), activation='relu'))
        model.add(ZeroPadding2D((1,1)))
        model.add(Convolution2D(512, (3, 3), activation='relu'))
        model.add(MaxPooling2D((2,2), strides=(2,2)))

        model.add(ZeroPadding2D((1,1)))
        model.add(Convolution2D(512, (3, 3), activation='relu'))
        model.add(ZeroPadding2D((1,1)))
        model.add(Convolution2D(512, (3, 3), activation='relu'))
        model.add(ZeroPadding2D((1,1)))
        model.add(Convolution2D(512, (3, 3), activation='relu'))
        model.add(MaxPooling2D((2,2), strides=(2,2)))

        model.add(Convolution2D(4096, (7, 7), activation='relu'))
        model.add(Dropout(0.5))
        model.add(Convolution2D(4096, (1, 1), activation='relu'))
        model.add(Dropout(0.5))
        model.add(Convolution2D(2622, (1, 1)))
        model.add(Flatten())
        model.add(Activation('softmax'))
        
        return model

    def _setup_model(self, num_classes):
        baseModel = self.baseModel()
        base_model_output = Sequential()
        base_model_output = Convolution2D(num_classes, (1, 1), name='predictions')(baseModel.layers[-4].output)
        base_model_output = Flatten()(base_model_output)
        base_model_output = Activation('softmax')(base_model_output)
        model = Model(inputs=baseModel.input, outputs=base_model_output)
        return model


    def _setup_gender_model(self):
        classes = 2
        self.gender_model = self._setup_model(2)
        self.gender_model.load_weights('models/facial/gender_model_weights.h5')


    def _setup_age_model(self):
        self.age_model = self._setup_model(101)
        self.age_model.load_weights('models/facial/age_model_weights.h5')

    def predict_age(self, face_image: Image):
        face = face_image.resize((224, 224))
        pixels = keras.preprocessing.image.img_to_array(face)
        pixels = numpy.expand_dims(pixels, axis = 0)
        pixels /= 255
        predictions = self.age_model.predict(pixels)[0,:] 
        apparent_age = numpy.sum(predictions * self.output_indexes)
        return apparent_age

    def predict_gender(self, face_image: Image):
        face = face_image.resize((224, 224))
        pixels = keras.preprocessing.image.img_to_array(face)
        pixels = numpy.expand_dims(pixels, axis = 0)
        pixels /= 255
        predictions = self.gender_model.predict(pixels)[0,:] 
        gender = "female" if numpy.argmax(predictions) == 0 else "male" 
        return gender