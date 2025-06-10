
import cocotb 
from cocotb.triggers import Timer , ClockCycles,RisingEdge, ReadOnly ,NextTimeStep , ReadWrite, FallingEdge, Event
from cocotb_bus.drivers import BusDriver
from cocotb_bus.monitors import BusMonitor
from cocotb_coverage.coverage  import CoverCross, CoverPoint , coverage_db
import os
from cocotb.log  import logging,SimLog

from cocotb.clock import Clock
import constraint
import random as rnd





@CoverPoint("top.a", #noqa F405
            xf=lambda x, y: x,
            bins=[0,1]
            
)

@CoverPoint("top.b", #noqa F405
            xf=lambda x,y: y,
            bins=[0,1]
            
)

@CoverCross("top.cross.ab", 
            items=["top.a", "top.b"]
            
            
)
def ab_cover(x,y):
    pass



@CoverPoint("top.w.wd_addr",
            xf=lambda wd_addr ,wd_en,wd_data,rd_en,rd_addr:wd_addr,
            bins=[4,5]
            )
@CoverPoint("top.w.wd_data",
            xf=lambda wd_addr ,wd_en,wd_data,rd_en,rd_addr:wd_data,
            bins=[0,1]
            )
@CoverPoint("top.w.wd_en",
            xf=lambda wd_addr ,wd_en,wd_data,rd_en,rd_addr:wd_en,
            bins=[0,1]
            )
@CoverPoint("top.r.rd_addr",
            xf=lambda wd_addr ,wd_en,wd_data,rd_en,rd_addr:rd_addr,
            bins=[0,1,2,3]
            )
@CoverPoint("top.r.rd_en",
            xf=lambda wd_addr ,wd_en,wd_data,rd_en,rd_addr:rd_en,
            bins=[0,1]
            )

@CoverCross("top.cross.w",
            items=["top.w.wd_addr" , "top.w.wd_data", "top.w.wd_en"]
          
            )
@CoverCross("top.cross.r",
            items=["top.r.rd_en" , "top.r.rd_addr"])



def addr_cover(wd_addr, wd_en, wd_data, rd_en, rd_addr):
    pass

# def a_prot_cover(txn):
#     pass



class WriteDriver(BusDriver):
    _signals = ['CLK','RST_N','write_address', 'write_data', 'write_en', 'write_rdy']
    def __init__(self, name,entity):
        #BusDriver.__init__(self, name,entity)
        self.name = name
        self.entity = entity
        self.CLK=entity.CLK   

    async def _driver_send(self, transaction, sync = True):
        await RisingEdge(self.CLK)
        if (self.entity.write_rdy.value.integer != 1):
            await RisingEdge(self.entity.write_rdy)
        
        self.entity.write_en.value =1
        self.entity.write_address.value = transaction.get('addr')
        self.entity.write_data.value = transaction.get('val')
        await RisingEdge(self.CLK)
        self.entity.write_en.value = 0


class ReadDriver(BusDriver):
    _signals = ['CLK','RST_N','read_address','read_en','read_rdy','read_data']
    def __init__(self, name,entity):
        #BusDriver.__init__(self, name,entity)
        self.name = name
        self.entity=entity
        self.CLK=entity.CLK

    async def _driver_send(self, transaction, sync = True):
        await RisingEdge(self.CLK)
        if (self.entity.read_rdy.value.integer != 1):
             await RisingEdge(self.entity.read_rdy)
        
        self.entity.read_en.value =1
        self.entity.read_address.value = transaction.get('addr')
        #self.entity.write_data.value = transaction.get('val')
        await RisingEdge(self.CLK)
        self.entity.read_en.value = 0


class dut_test:
    def __init__(self,name,entity,log):
        self.log=log
        self.name = name
        self.entity = entity
        #self.CLK = self.entity.CLK
        # self.a_ls =[]
        # self.b_ls =[]
        # self.y_ls =[]
        self.stats=[]
        self.writer_event = Event()
        self.reader_event = Event()
        #self.ref_address = {'Astatus':0 , 'Bstatus':1, 'Ystatus':2 ,'Youtput':3 , 'Adata':4, 'Bdata':5}
        self.writer = WriteDriver("write fifo", entity)
        self.reader = ReadDriver("read fifo", entity)

    # async def reset_dut(self):
    #     await RisingEdge(self.CLK)
    #     self.entity.write_address.value = 0
    #     self.entity.write_data.value = 0
    #     self.entity.write_en.value = 0
    #     self.entity.read_en.value = 0
    #     self.entity.read_data.value = 0
    #     self.entity.read_address.value = 0
    #     self.entity.RST_N.value = 1
    #     await ClockCycles(self.CLK,4)
    #     self.entity.RST_N.value = 0
    #     await ClockCycles(self.CLK,4)
    #     self.entity.RST_N.value = 1
    #     await RisingEdge (self.CLK)
    #     print(" reset done")
    
    def stat_dec(self,addr,val):
        if addr == 3 :
            self.stats.append({'name':'yresult', 'val': val})
        elif addr == 4:
            self.stats.append({'name':'awrite', 'val': val})
        elif addr == 5 :
            self.stats.append({'name':'bwrite', 'val': val})
        elif addr == 0 :
            self.stats.append({'name':'astatus', 'val':(f"{'full'if val == 0 else 'empty'}")})
        elif addr == 1 :
            self.stats.append({'name':'bstatus', 'val': (f"{'full'if val == 0 else 'empty'}")})
        
        elif addr == 2 :
            self.stats.append({'name':'ystatus', 'val': (f"{'full'if val == 1 else 'empty'}")})
         

    def cover(self):
        self.p = constraint.Problem()
        self.p.addVariable('write_en',[0,1])
        self.p.addVariable('read_en',[0,1])
        self.p.addVariable('write_address', [4,5])
        self.p.addVariable('read_address', [0,1,2,3])
        self.p.addVariable('write_data',[0,1])
        self.p.addVariable('write_rdy',[1])
        self.p.addVariable('read_rdy',[1])


        self.p.addConstraint(lambda rd_en, wd_en,rd_rdy: rd_en == 1 if wd_en ==0 and rd_rdy == 1 else rd_en == 0 , ['read_en','write_en', 'read_rdy'])

        self.p.addConstraint(lambda rd_en, wd_en,wd_rdy: wd_en == 1 if rd_en ==0 and wd_rdy == 1 else wd_en == 0 , ['read_en','write_en', 'write_rdy'])

    def solve(self):
        self.cover_obj = self.cover()
        self.sols = self.p.getSolutions()


    def get_sols(self):
        return rnd.choice(self.sols) if self.sols else None



@cocotb.test()
async def duttest(dut):
    cocotb.start_soon(Clock(dut.CLK, 2, units="ns").start())
    log = SimLog ("interface_test")
    logging.getLogger().setLevel(logging.INFO)

    tbh = dut_test(name='dut test', entity=dut , log = log)

    #await tbh.reset_dut()

    await tbh.writer._driver_send(transaction={'addr':4,'val' :0})
    await tbh.writer._driver_send(transaction={'addr':5,'val' :0})
    ab_cover(0,0)
    await tbh.reader._driver_send({'addr':3,'val':0})
    log.info(f"[functional] a:0 b:0 y:{dut.read_data.value.integer}")

    await tbh.writer._driver_send(transaction={'addr':4,'val' :0})
    await tbh.writer._driver_send(transaction={'addr':5,'val' :1})
    ab_cover(0,1)
    await tbh.reader._driver_send({'addr':3,'val':0})
    log.info(f"[functional] a:0 b:1 y:{dut.read_data.value.integer}")

    await tbh.writer._driver_send(transaction={'addr':4,'val' :1})
    await tbh.writer._driver_send(transaction={'addr':5,'val' :0})
    ab_cover(1,0)
    await tbh.reader._driver_send({'addr':3,'val':0})
    log.info(f"[functional] a:1 b:0 y:{dut.read_data.value.integer}")


    await tbh.writer._driver_send(transaction={'addr':4,'val' :1})
    await tbh.writer._driver_send(transaction={'addr':5,'val' :1})
    ab_cover(1,1)
    await tbh.reader._driver_send({'addr':3,'val':0})
    log.info(f"[functional] a:1 b:1 y:{dut.read_data.value.integer}")



    tbh.solve()
    for i in range (32):
        x= tbh.get_sols()
        addr_cover(x.get("write_address"), x.get("write_data"), x.get("write_en"), x.get("read_en"), x.get("read_address"))
        if x.get('read_en') ==1:
            await tbh.reader._driver_send(transaction={'addr':x.get('read_address'),"val":0})
            log.info(f"[{i}][read  operation] address: {x.get('read_address') } got data:{dut.read_data.value.integer}")
            tbh.stat_dec(x.get('read_address'), dut.read_data.value.integer)
        elif x.get('write_en') ==1:
            await tbh.writer._driver_send(transaction={'addr' :x.get('write_address') , 'val': x.get('write_data')})
            log.info(f"[{i}][write  operation] address :{x.get('write_address')} put data: {x.get('write_data')}")
            tbh.stat_dec(x.get('write_address'), x.get('write_data'))
        await RisingEdge(dut.CLK)


    for i in tbh.stats:
         log.info(f"{i}")

    
    coverage_db.report_coverage(log.info, bins = True)
    log.info(f"functional Coverage: {coverage_db['top.cross.ab'].cover_percentage:.2f}%")
    log.info(f"Write Coverage: {coverage_db['top.cross.w'].cover_percentage:.2f}%")
    log.info(f"Read Coverage: {coverage_db['top.cross.r'].cover_percentage:.2f}%")




