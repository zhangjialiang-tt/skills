// Adapt package and entry scope to the existing project. Not a Stream example.
import spinal.core._
import spinal.core.sim._

class ModAdd8 extends Component {
  val io = new Bundle {
    val a, b = in UInt(8 bits)
    val sum = out UInt(8 bits)
  }
  // Contract: unsigned addition modulo 256.
  io.sum := (io.a +^ io.b).resize(8)
}

object SimTemplate extends App {
  SimConfig.withVerilator.compile(new ModAdd8).doSim { dut =>
    // Simulation time units, not clock cycles. This DUT is combinational.
    SimTimeout(10000)
    val random = new scala.util.Random(42L)
    val directed = Seq((0, 0), (255, 1), (255, 255), (127, 128))
    val vectors = directed ++ Seq.fill(100)(
      (random.nextInt(256), random.nextInt(256)))
    var checked = 0
    for ((a, b) <- vectors) {
      dut.io.a #= a
      dut.io.b #= b
      sleep(1)
      val expected = (BigInt(a) + BigInt(b)) & BigInt(255)
      assert(dut.io.sum.toBigInt == expected, s"a=$a b=$b expected=$expected")
      checked += 1
    }
    assert(checked == vectors.size && checked > 0)
    println(s"CHECKED=$checked SEED=42 COMPLETE")
    simSuccess()
  }
}
