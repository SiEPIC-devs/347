import asyncio
from NIR.nir_controller_practical import Agilent8163Controller

import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_connect():
    # First lets test the connection... does it work
    controller = Agilent8163Controller(com_port=5)

    conn = controller.connect()
    
    if conn:
        logger.info("CONNECTION SUCCESSFULL YIPPY")
    else:
        logger.info("CONNECTION FAILED :(")
        return False

    disconn = controller.disconnect()

    if disconn:
        logger.info("DISCONNECT SUCCESSFUL TOO!")
    else:
        logger.info("DISCONNECTION FAILED:(")
        return False
    return True


async def runner():
    """Run all tests in sequence"""
    print("Starting Test Runner")
    print("=" * 50)
    
    try:
        # Run all test suites
        init_success = await test_connect()
        
        if init_success:
            pass
        else:
            print("❌ Initialization failed, skipping other tests")
        
        print("\n" + "=" * 50)
        print("🏁 Test sequence complete!")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        
    finally:
        print("\n🧹 Cleaning up...")
        print("✓ Cleanup complete")

if __name__ == "__main__":
    asyncio.run(runner())    
