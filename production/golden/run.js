const AP = require('argparse').ArgumentParser
const L  = require('./lib')

main = async (m, s) => {
  var [browser, page] = await L.init()
  var [result, page]  = await L.run(page, m, s)
  await browser.close()
  console.log(L.normalizeResult(result))
  return 
}

// TODO: add a an example
const descr = "run.js is a CLI script to run submissions against reference implementation."

var ap = new AP({
  version: "0.0.1",
  addHelp: true,
  description: descr
})

ap.addArgument(
  ['-m', '--map'],
  {help: "Path to a .desc file",
   required: true}
)

ap.addArgument(
  ['-s', '--solution'],
  {help: "Path to a .sol file",
   required: true}
)

const args = ap.parseArgs()

main(args.map, args.solution)
