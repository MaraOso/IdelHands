from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import uic, QtWidgets
import HandDetector
import numpy as np
import pyautogui
import autopy
import time
import cv2
import sys


class UI(QtWidgets.QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi('idelHands.ui', self)

        self.wCamV = 640
        self.hCamV = 480
        self.frameReductionV = 100
        self.smootheningV = 5
        self.camCaptureV = 0
        self.maxHandsV = 1
        self.detectorConfidenceV = 0.7
        self.webcamShowV = False

        self.startBtn.clicked.connect(self.startApp)
        self.stopBtn.clicked.connect(self.stopApp)

        self.show()

    def startApp(self):
        self.wCamV = self.wCam.value()
        self.hCamV = self.hCam.value()
        self.frameReductionV = self.frameReduction.value()
        self.smootheningV = self.smoothening.value()
        self.camCaptureV = self.camCapture.value()
        self.maxHandsV = self.maxHands.value()
        self.detectorConfidenceV = self.detectorConfidence.value() * .01
        self.webcamShowV = self.webCamShow.isChecked()
        self.app = Application(wCam=self.wCamV, hCam=self.hCamV, frameReduction=self.frameReductionV, smoothening=self.smootheningV,
                               camCapture=self.camCaptureV, maxHands=self.maxHandsV, detectorConfidence=self.detectorConfidenceV, webCamShow=self.webcamShowV)
        self.app.App()

    def stopApp(self):
        del self.app


class Application():
    def __init__(self, wCam=640, hCam=480, frameReduction=100, smoothening=5, camCapture=0, maxHands=1, detectorConfidence=0.7, webCamShow=False):
        self.wCam = wCam
        self.hCam = hCam
        self.frameReduction = frameReduction
        self.smoothening = smoothening
        self.camCapture = camCapture
        self.maxHands = maxHands
        self.detectorConfidence = detectorConfidence
        self.webCamShow = webCamShow

        self.prevLocX, self.prevLocY = 0, 0
        self.currLocX, self.currLocY = 0, 0

        self.applicationRunning = False

    def App(self):
        self.applicationRunning = True
        cap = cv2.VideoCapture(self.camCapture)
        cap.set(3, self.wCam)
        cap.set(4, self.hCam)

        detector = HandDetector.HandDetector(
            maxHands=self.maxHands, detectionConfidence=self.detectorConfidence)
        wScr, hScr = autopy.screen.size()

        evalTime = time.time()
        openHandTime = 0
        prevTime = time.time()
        accumulatedTime = 0

        fingerPositions = []
        monitoring = False

        while self.applicationRunning:
            success, img = cap.read()
            img = detector.findHands(img)
            lmList, bbox = detector.findPosition(img)

            if len(lmList) != 0:
                accumulatedTime = prevTime - time.time()
                prevTime = time.time()
                if accumulatedTime > .3:
                    if len(fingerPositions) != 0:
                        fingerPositions.pop(0)
                    accumulatedTime = 0

                x1, y1, z1 = lmList[8][1:]
                fingers = detector.fingersUp()

                if monitoring:
                    if fingers[3] == 0 and 3 in fingerPositions:
                        pyautogui.keyDown('ctrl')
                        pyautogui.keyDown("win")
                        pyautogui.keyDown('o')
                        time.sleep(.1)
                        pyautogui.keyUp('ctrl')
                        pyautogui.keyUp("win")
                        pyautogui.keyUp('o')
                        fingerPositions = []
                    elif fingers[2] == 0 and 2 in fingerPositions:
                        pyautogui.click(button='right')
                        fingerPositions = []
                    elif fingers[1] == 0 and 1 in fingerPositions:
                        autopy.mouse.click()
                        fingerPositions = []

                    if fingers[1] == 1:
                        fingerPositions.append(1)
                        x3 = np.interp(x1, (self.frameReduction, self.wCam -
                                            self.frameReduction), (0, wScr))
                        y3 = np.interp(y1, (self.frameReduction, self.hCam -
                                            self.frameReduction), (0, hScr))

                        self.currLocX = self.prevLocX + \
                            (x3 - self.prevLocX) / self.smoothening
                        self.currLocY = self.prevLocY + \
                            (y3 - self.prevLocY) / self.smoothening

                        autopy.mouse.move(wScr - self.currLocX, self.currLocY)
                        self.prevLocX, self.prevLocY = self.currLocX, self.currLocY

                    if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
                        fingerPositions.append(3)
                    elif fingers[1] == 1 and fingers[2] == 1:
                        fingerPositions.append(2)

                if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
                    openHandTime += time.time() - evalTime
                    # print(openHandTime)
                    if openHandTime > 5:
                        openHandTime = 0
                        monitoring = not monitoring
                        fingerPositions = []
                    evalTime = time.time()

            if self.webCamShow:
                cv2.rectangle(img, (self.frameReduction, self.frameReduction), (self.wCam -
                                                                                self.frameReduction, self.hCam - self.frameReduction), (255, 0, 255), 2)
                cv2.imshow("Idle Hands", img)

            cv2.waitKey(1)


def main():
    app = QApplication(sys.argv)

    window = UI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
