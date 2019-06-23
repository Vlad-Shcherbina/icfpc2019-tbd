const AP = require('argparse').ArgumentParser
const L  = require('./lib')

main = async (m, s, b) => {
  var [browser, page] = await L.init()
  var [result, page]  = await L.run(page, m, s)
  await browser.close()
  console.log(L.normalizeResult(result))
  return 
}

mainPuz = async (m, s) => {
  var [browser, page] = await L.init()
  var [result, page]  = await L.puz(page, m, s)
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
  ['-b', '--boosters'],
  {help: "Buy stuff with lambdacoins",
   required: false}
)

ap.addArgument(
  ['-m', '--map'],
  {help: "Path to a .desc file",
   required: false}
)

ap.addArgument(
  ['-s', '--solution'],
  {help: "Path to a .sol file",
   required: false}
)

ap.addArgument(
  ['-d', '--description'],
  {help: "Path to generated .desc file",
   required: false}
)

ap.addArgument(
  ['-c', '--condition'],
  {help: "Path to a .cond file",
   required: false}
)

const args = ap.parseArgs()

if (args.map && args.solution) {
  main(args.map, args.solution, args.boosters)
}

if (args.condition && args.description) {
  mainPuz(args.condition, args.description)
}
