from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QDialog
from PyQt6.QtWidgets import QWidget,QToolButton 
from PyQt6.QtWidgets import QMessageBox,QVBoxLayout
from PyQt6.QtWidgets import QCheckBox,QButtonGroup,QGridLayout, QSpinBox, QSlider, QLabel
from PyQt6 import uic
from helper import res_path,classlistToIds,updateClassComboBox,qtBlockAndCall,throttle
from PyQt6.QtCore import QTimer,QEvent
import main
from base_ui import WidgetUI,CommunicationHandler

class WheelUI(WidgetUI,CommunicationHandler):

    def __init__(self, main: 'main.MainUi'=None, unique=0):
        WidgetUI.__init__(self, main, 'wheel.ui')
        CommunicationHandler.__init__(self)


        self.cpr = -1

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timer_cb)
        

        ### Event management with board message
        # General FFB Section
        self.horizontalSlider_fxratio.valueChanged.connect(lambda val : self.sliderChanged_UpdateLabel(val,self.label_fxratio,"{:2.2f}%",1/255,"axis","fxratio"))
        self.horizontalSlider_degrees.valueChanged.connect(lambda val : self.sliderChanged_UpdateSpinbox(val,self.spinBox_range,1,"axis","degrees"))
        self.spinBox_range.valueChanged.connect(lambda val : self.spinboxChanged_UpdateSlider(val,self.spinBox_range,1))
        
        # Mechanical section
        self.horizontalSlider_idle.valueChanged.connect(lambda val : self.sliderChanged_UpdateSpinbox(val, self.spinBox_idlespring,1,"axis","idlespring"))
        self.spinBox_idlespring.valueChanged.connect(lambda val : self.spinboxChanged_UpdateSlider(val,self.horizontalSlider_idle,1,))
        self.horizontalSlider_perma_damper.valueChanged.connect(lambda val : self.sliderChanged_UpdateSpinbox(val, self.spinBox_perma_damper,1,"axis","axisdamper"))
        self.spinBox_perma_damper.valueChanged.connect(lambda val : self.spinboxChanged_UpdateSlider(val,self.horizontalSlider_perma_damper,1))
        self.horizontalSlider_perma_inertia.valueChanged.connect(lambda val : self.sliderChanged_UpdateSpinbox(val, self.spinBox_perma_inertia,1,"axis","axisinertia"))
        self.spinBox_perma_inertia.valueChanged.connect(lambda val : self.spinboxChanged_UpdateSlider(val,self.horizontalSlider_perma_inertia,1))
        self.horizontalSlider_perma_friction.valueChanged.connect(lambda val : self.sliderChanged_UpdateSpinbox(val, self.spinBox_perma_friction,1,"axis","axisfriction"))
        self.spinBox_perma_friction.valueChanged.connect(lambda val : self.spinboxChanged_UpdateSlider(val,self.horizontalSlider_perma_friction,1))
        
        """
        self.horizontalSlider_damper.valueChanged.connect(lambda val : self.send_value("axis","axisdamper",val,instance=self.axis))
        self.horizontalSlider_friction.valueChanged.connect(lambda val : self.send_value("axis","axisfriction",val,instance=self.axis))
        self.horizontalSlider_inertia.valueChanged.connect(lambda val : self.send_value("axis","axisinertia",val,instance=self.axis))
        # FFB Settings
        self.horizontalSlider_cffilter.valueChanged.connect(self.cffilter_changed)
        self.horizontalSlider_spring.valueChanged.connect(lambda val : self.sliderChangedUpdateSpinbox(val,self.doubleSpinBox_spring,self.springgain/256,"spring"))
        self.horizontalSlider_damper.valueChanged.connect(lambda val : self.sliderChangedUpdateSpinbox(val,self.doubleSpinBox_damper,self.dampergain/256,"damper"))
        self.horizontalSlider_damper.valueChanged.connect(self.display_speed_cutoff_damper)
        self.horizontalSlider_friction.valueChanged.connect(lambda val : self.sliderChangedUpdateSpinbox(val,self.doubleSpinBox_friction,self.frictiongain/256,"friction"))
        self.horizontalSlider_friction.valueChanged.connect(self.display_speed_cutoff_friction)
        self.horizontalSlider_inertia.valueChanged.connect(lambda val : self.sliderChangedUpdateSpinbox(val,self.doubleSpinBox_inertia,self.inertiagain/256,"inertia"))
        self.horizontalSlider_inertia.valueChanged.connect(self.display_accel_cutoff_inertia)
        ### """
        
        self.register_callback("axis","fxratio",lambda val : self.dataChanged_UpdateSliderAndLabel(val,self.horizontalSlider_fxratio, self.label_fxratio, "{:2.2%}", 1/255),0,int)
        self.register_callback("axis","degrees",lambda val : self.dataChanged_UpdateSliderAndSpinbox(val,self.horizontalSlider_degrees,self.spinBox_range,1),0,int)
        
        self.register_callback("axis","idlespring",lambda val : self.dataChanged_UpdateSliderAndSpinbox(val,self.horizontalSlider_idle,self.spinBox_idlespring,1),0,int)
        self.register_callback("axis","axisdamper",lambda val : self.dataChanged_UpdateSliderAndSpinbox(val,self.horizontalSlider_perma_damper,self.spinBox_perma_damper,1),0,int)
        self.register_callback("axis","axisinertia",lambda val : self.dataChanged_UpdateSliderAndSpinbox(val,self.horizontalSlider_perma_inertia,self.spinBox_perma_inertia,1),0,int)
        self.register_callback("axis","axisfriction",lambda val : self.dataChanged_UpdateSliderAndSpinbox(val,self.horizontalSlider_perma_friction,self.spinBox_perma_friction,1),0,int)
        
        self.register_callback("axis","pos",self.enc_pos_cb,0,int)
        self.register_callback("axis","cpr",self.cpr_cb,0,int)


    def init_ui(self):
        try:
            self.send_commands("axis",["cpr","pos","degrees", "fxratio", "idlespring", "axisdamper", "axisinertia", "axisfriction"])
        except:
            self.main.log("Error initializing Wheel tab")
            return False
        return True
    
    # Tab is currently shown
    def showEvent(self,event):
        self.init_ui() # update everything
        self.timer.start(500)

    # Tab is hidden
    def hideEvent(self,event):
        self.timer.stop()

    # Timer interval reached
    def timer_cb(self):
        if self.cpr > 0:
            self.send_command("axis","pos",0, typechar='?')
        elif self.cpr == -1:
            # cpr invalid. Request cpr
            self.send_command("axis","cpr",0, typechar='?')
    
    #######################################################################################################
    #                                            Windows Event
    #######################################################################################################
    
       
    @throttle(50)
    def sliderChanged_UpdateSpinbox(self, val : int, spinbox : QSpinBox, factor :float, cls : str=None, command : str=None):
        """when a slider move, and it provide a command, the slider update de spinbox
        and send to the board the Value

        Args:
            val (int): new value of the slider
            spinbox (QtSpinbox): the spinbox to refresh
            factor (float): the scale factor between slider and spinbox
            cls (string): name of the class to send the command (on the board)
            command (string, optional): the command to send to the board. Defaults to None.
        """
        newVal = val * factor
        if(spinbox.value() != newVal):
            qtBlockAndCall(spinbox, spinbox.setValue,newVal)
        if(command):
            self.send_value(cls,command,val)
    
    def spinboxChanged_UpdateSlider(self, val : float, slider : QSlider, factor : float):
        newVal = int(round(val * factor))
        if (slider.value() != newVal) :
            slider.setValue(newVal)
            
    def dataChanged_UpdateSliderAndSpinbox(self,val : float,slider : QSlider,spinbox : QSpinBox,factor : float):
        newval = int(round(val,1))
        qtBlockAndCall(slider, slider.setValue, newval)
        qtBlockAndCall(spinbox, spinbox.setValue,newval * factor)
        
        pass
        
    @throttle(50)
    def sliderChanged_UpdateLabel(self, val : int, label : QLabel, pattern :str, factor: float, cls : str=None, command : str=None):
        """when a slider move, and it provide a command, the slider update de spinbox
        and send to the board the Value

        Args:
            val (int): new value of the slider
            spinbox (QtSpinbox): the spinbox to refresh
            factor (float): the scale factor between slider and spinbox
            cls (string): name of the class to send the command (on the board)
            command (string, optional): the command to send to the board. Defaults to None.
        """
        newVal = val * factor
        chaine = pattern.format(newVal)
        if(label.text != chaine):
            qtBlockAndCall(label, label.setText,chaine)
        if(command):
            self.send_value(cls,command,val)
    
    def dataChanged_UpdateSliderAndLabel(self,val : float,slider : QSlider, label : QLabel, pattern : str, factor : float):
        newval = int(round(val))
        qtBlockAndCall(slider, slider.setValue, newval)
        self.sliderChanged_UpdateLabel(newval,label,pattern, factor)
        
            
    #######################################################################################################
    #                                            Board CallBack
    #######################################################################################################
    
    def cpr_cb(self,val : int):
        if val > 0:
            self.cpr = val
        
    def enc_pos_cb(self,val : int):
        if self.cpr > 0:
            rots = val / self.cpr
            degs = rots * 360
            self.doubleSpinBox_curdeg.setValue(degs)
