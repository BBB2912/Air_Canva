import cv2 as cv
import numpy as np
import mediapipe as mp

class AirCanvas:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draws = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.frame_width = 1300
        self.frame_height = 700
        self.video = cv.VideoCapture(0)
        self.video.set(cv.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.video.set(cv.CAP_PROP_FRAME_HEIGHT, self.frame_height)

        cv.namedWindow("AIR CANVAS", cv.WINDOW_NORMAL)
        cv.resizeWindow("AIR CANVAS", self.frame_width, self.frame_height)

        cv.waitKey(1)

        self.tools = cv.imread(r".\static\images\tools.png", cv.IMREAD_UNCHANGED)
        self.tools = self.tools.astype('uint8')
        self.tools = cv.cvtColor(self.tools, cv.COLOR_BGR2RGB)

        self.colors = {
            'Red': (0, 0, 255),
            'Blue': (255, 0, 0),
            'Green': (0, 255, 0),
            'Yellow': (0, 255, 255),
            'White': (255, 255, 255),
            'Black': (0, 0, 0)
        }
        self.colors_cordinates = {
            'Red': {'Origin': (1200, 40)},
            'Blue': {'Origin': (1200, 120)},
            'Green': {'Origin': (1200, 200)},
            'Yellow': {'Origin': (1200, 280)},
            'White': {'Origin': (1200, 360)},
        }
        self.Box_cordinates = {
            'Eraser': {'Start': (510, 5), 'End': (600, 110)},
            'Circle': {'Start': (620, 5), 'End': (700, 110)},
            'Square': {'Start': (720, 5), 'End': (800, 110)},
            'Line': {'Start': (820, 5), 'End': (900, 110)},
            'FreeStyle': {'Start': (920, 10), 'End': (1000, 110)},
        }

        self.mask = np.zeros((720, 1280, 3), dtype=np.uint8)
        self.fontFace = cv.FONT_HERSHEY_SIMPLEX
        self.fontScale = 1
        self.current_tool = 'FreeStyle'
        self.write_color = 'Red'
        self.var_init = False
        self.x0, self.y0 = 0, 0
        self.thick = 6

        cv.createTrackbar('Pen Thickness', 'AIR CANVAS', self.thick, 15, self.on_trackbar)

    def on_trackbar(self, val):
        self.thick = val

    def draw_circles(self, frame, origin, color, radius, thickness):
        return cv.circle(frame, origin, radius, color, thickness)

    def get_tool(self, x, y):
        if y < 130 and x > 500:
            if x < 600:
                return 'Eraser'
            elif x < 700:
                return 'Circle'
            elif x < 800:
                return 'Square'
            elif x < 900:
                return 'Line'
            elif x < 1000:
                return 'FreeStyle'
        return self.current_tool

    def get_color(self, x, y):
        if x > 1100:
            if y < 80:
                return 'Red'
            elif y < 160:
                return 'Blue'
            elif y < 240:
                return 'Green'
            elif y < 320:
                return 'Yellow'
            elif y < 400:
                return 'White'
        return self.write_color

    def index_raised(self, yi, y9):
        return (yi - y9) > 40

    def run(self):
        while True:
            res, frame = self.video.read()
            frame = cv.flip(frame, 1)

            main_frame = frame.copy()
            main_frame[0:self.tools.shape[0], 500:500+self.tools.shape[1]] = self.tools

            

            for color, cordinates in self.colors_cordinates.items():
                main_frame = self.draw_circles(main_frame, cordinates['Origin'], self.colors[color], 30, -1)

            main_frame = cv.cvtColor(main_frame, cv.COLOR_BGR2RGB)
            results = self.hands.process(main_frame)
            main_frame = cv.cvtColor(main_frame, cv.COLOR_RGB2BGR)
            self.thick = cv.getTrackbarPos('Pen Thickness', 'AIR CANVAS')
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draws.draw_landmarks(main_frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS, self.mp_drawing_styles.get_default_hand_landmarks_style())

                    index_finger_tip = hand_landmarks.landmark[8]
                    h, w, _ = frame.shape
                    x1 = int(index_finger_tip.x * w)
                    y1 = int(index_finger_tip.y * h)
                    print(x1, y1)

                    self.current_tool = self.get_tool(x1, y1)
                    self.write_color = self.get_color(x1, y1)

                    cv.rectangle(main_frame, self.Box_cordinates[self.current_tool]['Start'], self.Box_cordinates[self.current_tool]['End'], self.colors['Red'], 3)

                    if self.write_color != 'Black':
                        main_frame = self.draw_circles(main_frame, self.colors_cordinates[self.write_color]['Origin'], self.colors['Black'], 40, 3)

                    x2, y2 = int(hand_landmarks.landmark[12].x*w), int(hand_landmarks.landmark[12].y*h)
                    y3 = int(hand_landmarks.landmark[9].y*h)

                    if self.current_tool == 'FreeStyle':
                        if self.index_raised(y2, y3):
                            if self.x0 == 0 and self.y0 == 0:
                                self.x0, self.y0 = x1, y1

                            cv.circle(main_frame, (x1, y1), 10, self.colors[self.write_color], -1)
                            cv.circle(main_frame, (x1, y1), 15, self.colors[self.write_color], 2)
                            cv.line(self.mask, (self.x0, self.y0), (x1, y1), self.colors[self.write_color], self.thick)

                            self.x0, self.y0 = x1, y1
                        else:
                            self.x0 = x1
                            self.y0 = y1

                    elif self.current_tool == 'Line':
                        if self.index_raised(y2, y3):
                            if not self.var_init:
                                self.xii, self.yii = x1, y1
                                self.var_init = True

                            cv.line(main_frame, (self.xii, self.yii), (x1, y1), self.colors[self.write_color], self.thick)
                        else:
                            if self.var_init:
                                cv.line(self.mask, (self.xii, self.yii), (x1, y1), self.colors[self.write_color], self.thick)
                                self.var_init = False

                    elif self.current_tool == 'Square':
                        if self.index_raised(y2, y3):
                            if not self.var_init:
                                self.xs, self.ys = x1, y1
                                self.var_init = True

                            cv.rectangle(main_frame, (self.xs, self.ys), (x1, y1), self.colors[self.write_color], self.thick)
                        else:
                            if self.var_init:
                                cv.rectangle(self.mask, (self.xs, self.ys), (x1, y1), self.colors[self.write_color], self.thick)
                                self.var_init = False

                    elif self.current_tool == 'Circle':
                        if self.index_raised(y2, y3):
                            if not self.var_init:
                                self.xc, self.yc = x1, y1
                                self.var_init = True

                            radius = int(((x1 - self.xc) ** 2 + (y1 - self.yc) ** 2) ** 0.5)
                            cv.circle(main_frame, (self.xc, self.yc), radius, self.colors[self.write_color], self.thick, lineType=cv.LINE_AA)
                        else:
                            if self.var_init:
                                cv.circle(self.mask, (self.xc, self.yc), radius, self.colors[self.write_color], self.thick, lineType=cv.LINE_AA)
                                self.var_init = False

                    elif self.current_tool == 'Eraser':
                        self.write_color = 'Black'
                        if self.index_raised(y2, y3):
                            print('Erase')
                            if self.x0 == 0 and self.y0 == 0:
                                self.x0, self.y0 = x1, y1

                            cv.circle(main_frame, (x1, y1), 20, self.colors[self.write_color], -1)
                            cv.circle(main_frame, (x1, y1), 30, self.colors['White'], 5)
                            cv.line(self.mask, (self.x0, self.y0), (x1, y1), self.colors[self.write_color], self.thick + 10)

                            self.x0, self.y0 = x1, y1
                        else:
                            self.x0 = x1
                            self.y0 = y1
            
            imgGray=cv.cvtColor(self.mask,cv.COLOR_BGR2GRAY)
            _,imginv=cv.threshold(imgGray,20,255,cv.THRESH_BINARY_INV)
            imginv=cv.cvtColor(imginv,cv.COLOR_GRAY2BGR)

            main_frame=cv.bitwise_and(main_frame,imginv)
            main_frame=cv.bitwise_or(main_frame,self.mask)

            
            cv.putText(main_frame, self.current_tool, (5, 60), self.fontFace, self.fontScale, self.colors[self.write_color], 2, lineType=cv.LINE_AA)
            cv.imshow("AIR CANVAS", main_frame)

            
            if cv.waitKey(5) & 0xFF == ord('d'):
                break

        self.video.release()
        cv.destroyAllWindows()

if __name__ == "__main__":
    canvas = AirCanvas()
    canvas.run()
