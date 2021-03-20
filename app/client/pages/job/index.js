import { useState } from 'react';
import nookies from 'nookies';
import firebaseClient from '../../utils/firebaseClient';
import { verifyIdToken } from '../../utils/firebaseAdmin';
import {
  Container,
  Link,
  Layout,
  FlexRow,
  FlexCol,
  FlexCenter,
  FormField,
  MathTex,
  Navbar,
  Modal,
} from '../../components';

const JobPageModal = ({ jobId, err, errMsg, isModalActive, setIsModelActive }) => {
  const buttonStyle =
    'px-6 py-2 text-base text-center rounded-lg cursor-pointer lg:transition lg:duration-300  text-white';
  return (
    <Modal isActive={isModalActive}>
      {!err && (
        <>
          <div className="mb-7">
            Job with id {jobId} created successfully. Start it by clicking the button in the job
            table.
          </div>
          <FlexCenter>
            <FlexRow className="space-x-3">
              <Link href="/job/results">
                <a className={buttonStyle + 'bg-purple-700 hover:bg-purple-900'}>View your jobs</a>
              </Link>
              <div
                className={buttonStyle + 'bg-blue-700 hover:bg-blue-900'}
                onClick={() => setIsModelActive(false)}
              >
                Go back to form
              </div>
            </FlexRow>
          </FlexCenter>
        </>
      )}
      {err && (
        <>
          <div className="mb-7">{errMsg}</div>
          <FlexCenter>
            <a
              className={
                'px-6 py-2 text-base text-center bg-purple-700  ' +
                ' rounded-lg cursor-pointer lg:transition lg:duration-300 hover:bg-purple-900 text-white'
              }
              onClick={() => setIsModelActive(false)}
            >
              Try again!
            </a>
          </FlexCenter>
        </>
      )}
    </Modal>
  );
};

const FieldDescription = ({ children, name, activeField, icon, math }) => (
  <div
    className={`${
      name.includes(activeField) ? 'text-blue-400' : ''
    } transition duration-200 my-1 lg:my-0`}
  >
    {icon && <i className={`${icon} mr-5`}></i>}
    {math && (
      <MathTex inline className="mr-5">
        {math}
      </MathTex>
    )}
    {children}
  </div>
);

const Descs = ({ activeField }) => (
  <FlexCol between className="w-full h-full">
    <FieldDescription activeField={activeField} name={['job_name']} icon="fas fa-bars">
      Job name: a unique key id for your job.
    </FieldDescription>
    <FieldDescription
      activeField={activeField}
      name={['max_replicas', 'initial_number_of_replicas']}
      icon="fas fa-cloud"
    >
      Max / initial N° replicas: maximum / initial number of replicas to use. The more replicas,
      the better the sampling, but the more compute quota you will use
    </FieldDescription>
    <FieldDescription
      activeField={activeField}
      name={['num_production_samples', 'num_optimization_samples']}
      icon="fas fa-stream"
    >
      N° production / optimization samples: number of MCMC samples in production / optimization
      runs
    </FieldDescription>
    <FieldDescription
      activeField={activeField}
      name={['tempered_distribution_family']}
      math="\{\mathbb{P}\}"
    >
      Tempered distribution family: the family of tempered distributions to use. For now, only
      tempering whole probabilities ("Boltzmann") is supported
    </FieldDescription>
    <FieldDescription activeField={activeField} name={['minimum_beta']} math="\beta_{min}">
      Beta min: the minimum inverse temperature (beta) which determines the flatness of the
      flattest distribution
    </FieldDescription>
    <FieldDescription activeField={activeField} name={['target_acceptance_rate']} math="\rho">
      Target acceptance rate: the acceptance rate between neigboring replicas that the algorithm
      aims to achieve. 0.2 is a good value.
    </FieldDescription>
    <FieldDescription
      activeField={activeField}
      name={['probability_definition']}
      icon="fas fa-link"
    >
      Probability definition: URL to zip archive including importable Python module providing the
      probability density
    </FieldDescription>
    <FieldDescription activeField={activeField} name={['dependencies']} icon="fas fa-bolt">
      Dependencies: comma-separated list of dependencies to install on compute nodes
    </FieldDescription>
  </FlexCol>
);

const OptionalFormSection = ({ children, active }) => (
  <FlexCol
    between
    className={`${
      active ? 'h-36' : 'opacity-0 h-0 pointer-events-none'
    } w-full transition-all duration-900 `}
  >
    {children}
  </FlexCol>
);

const Job = ({ authed }) => {
  firebaseClient();

  const [activeField, setActiveField] = useState('other');

  // Form fields state variables
  const [job_name, setJobName] = useState('my_sampling_job');
  const [max_replicas, setMaxReplicas] = useState(10);
  const [initial_number_of_replicas, setInitNReplicas] = useState(3);
  const [tempered_distribution_family, setTemperedDist] = useState('boltzmann');
  const [num_production_samples, setNumProductionSamples] = useState(10000);
  const [num_optimization_samples, setNumOptimizationSamples] = useState(3000);
  const [minimum_beta, setMinBeta] = useState(0.01);
  const [target_acceptance_rate, setTargetAcceptanceRate] = useState(0.2);
  const [probability_definition, setProbDef] = useState(
    'https://storage.googleapis.com/resaas-dev-public/mixture.zip'
  );
  const [dependencies, setDeps] = useState(['numpy', 'scipy']);

  const [createdJobId, setCreatedJobID] = useState(null);

  // Error handling states
  const [err, setErr] = useState(false);
  const [errMsg, setErrMsg] = useState('');

  // See more job form options
  const [seeMoreFields, setSeeMoreFields] = useState(false);

  // Active model state
  const [isModalActive, setIsModelActive] = useState(false);

  const createJob = async () => {
    const body = JSON.stringify({
      name: job_name,
      initial_number_of_replicas:
        seeMoreFields && initial_number_of_replicas
          ? initial_number_of_replicas
          : Math.max(2, Math.floor(max_replicas * 0.5)),
      max_replicas,
      tempered_dist_family: tempered_distribution_family,
      initial_schedule_parameters: {
        minimum_beta,
      },
      replica_exchange_parameters: {
        num_production_samples,
        num_optimization_samples:
          seeMoreFields && num_optimization_samples
            ? num_optimization_samples
            : Math.floor(num_production_samples * 0.25),
      },
      optimization_parameters: {
        optimization_quantity_target: target_acceptance_rate,
      },
      probability_definition,
      dependencies: [{ type: 'pip', deps: dependencies }],
    });

    const requestOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    };
    try {
      let response = await fetch('/api/job/create', requestOptions);
      let data = await response.json();
      if (response.ok && data.job_id) {
        setErr(false);
        setCreatedJobID(data.job_id);
        setIsModelActive(true);
      } else {
        setErr(true);
        setErrMsg(
          "Something went wrong. For more information, see your browser's console. Please contact our support team if you require assistance."
        );
        console.log(data);
        setIsModelActive(true);
      }
    } catch (e) {
      setErr(true);
      setErrMsg(
        "Something went wrong. For more information, see your browser's console. Please contact our support team if you require assistance."
      );
      console.log(e);
      setIsModelActive(true);
    }
  };

  if (authed)
    return (
      <Layout>
        <JobPageModal
          isModalActive={isModalActive}
          setIsModelActive={setIsModelActive}
          jobId={createdJobId}
          err={err}
          errMsg={errMsg}
        />
        <Container className="text-white bg-gradient-to-r from-purple-900 to-indigo-600 lg:h-screen font-body">
          <FlexCol between className="h-full">
            <Navbar />
            <FlexCenter className="w-full h-full py-5 md:py-20">
              <FlexCol center className="w-full h-full">
                <div className="mb-10 text-2xl md:text-5xl lg:text-6xl">
                  Run a sampling task
                  <i className="ml-3 fas fa-rocket"></i>
                </div>
                <div className="w-full mb-20 text-base md:text-xl lg:w-2/3 md:text-justify">
                  Every sampling job is specified through several parameters. This form is
                  populated with values for a simple example: a mixture of Gaussians in two
                  dimensions. If you like to define your own probability, download the example .zip
                  file and follow instructions in the source code. You can extract the samples from
                  your distribution from the downloaded results by using a script we provide here:{' '}
                  <a href="https://storage.googleapis.com/resaas-dev-public/concatenate_samples.py">
                    link
                  </a>
                </div>
                <FlexRow between responsive media="lg" className="w-full lg:h-4/5 lg:space-x-20">
                  <FlexCenter className="flex-grow mb-10 lg:py-10 h-96 md:h-80 lg:h-full lg:mb-0 w-96">
                    <form
                      className="h-full"
                      onSubmit={(e) => {
                        e.preventDefault();
                        if (!isModalActive) createJob(e);
                      }}
                    >
                      <FlexCol between className="h-56">
                        <FormField
                          label="Job name"
                          inputName="job_name"
                          setActiveField={setActiveField}
                          value={job_name}
                          onChange={(e) => setJobName(e.target.value)}
                        />
                        <FlexRow
                          responsive
                          media="md"
                          className="space-y-1 md:space-y-0 md:space-x-5"
                        >
                          <FormField
                            label="N° production samples"
                            inputName="num_production_samples"
                            inputType="number"
                            setActiveField={setActiveField}
                            minNumber={1000}
                            value={num_production_samples}
                            onChange={(e) => setNumProductionSamples(e.target.value)}
                          />
                          <FormField
                            label="Max N° replicas"
                            inputName="max_replicas"
                            inputType="number"
                            setActiveField={setActiveField}
                            minNumber={3}
                            value={max_replicas}
                            onChange={(e) => setMaxReplicas(e.target.value)}
                          />
                        </FlexRow>
                        <FormField
                          label="Probability definition"
                          inputName="probability_definition"
                          inputType="url"
                          setActiveField={setActiveField}
                          value={probability_definition}
                          onChange={(e) => setProbDef(e.target.value)}
                        />
                        <FormField
                          label="Dependencies"
                          inputName="dependencies"
                          inputType="text"
                          setActiveField={setActiveField}
                          value={dependencies}
                          onChange={(e) => setDeps(e.target.value.split(','))}
                          className="mb-5"
                        />
                      </FlexCol>
                      <OptionalFormSection active={seeMoreFields}>
                        <FlexRow
                          responsive
                          media="md"
                          className="space-y-1 md:space-y-0 md:space-x-5"
                        >
                          <FormField
                            optional
                            label="Initial N° replicas"
                            inputName="initial_number_of_replicas"
                            inputType="number"
                            setActiveField={setActiveField}
                            minNumber={3}
                            value={initial_number_of_replicas}
                            onChange={(e) => setInitNReplicas(e.target.value)}
                          />

                          <FormField
                            optional
                            label="N° optimzation samples"
                            inputName="num_optimization_samples"
                            inputType="number"
                            setActiveField={setActiveField}
                            minNumber={1000}
                            value={num_optimization_samples}
                            onChange={(e) => setNumOptimizationSamples(e.target.value)}
                          />
                        </FlexRow>
                        <FormField
                          optional
                          label="Tempered distribution family"
                          inputName="tempered_distribution_family"
                          hasDropdown
                          setActiveField={setActiveField}
                          disabled
                          defaultValue="Boltzmann"
                          value={tempered_distribution_family}
                          onChange={(e) => setTemperedDist(e.target.value)}
                        />
                        <FlexRow
                          responsive
                          media="md"
                          className="space-y-1 md:space-y-0 md:space-x-5"
                        >
                          <FormField
                            label="Beta min"
                            optional
                            inputName="minimum_beta"
                            inputType="number"
                            setActiveField={setActiveField}
                            minNumber={0}
                            maxNumber={1}
                            stepNumber={0.01}
                            value={minimum_beta}
                            onChange={(e) => setMinBeta(e.target.value)}
                          />
                          <FormField
                            optional
                            label="Target acceptance rate"
                            inputName="target_acceptance_rate"
                            inputType="number"
                            minNumber={0.1}
                            maxNumber={0.9}
                            stepNumber={0.1}
                            setActiveField={setActiveField}
                            value={target_acceptance_rate}
                            onChange={(e) => setTargetAcceptanceRate(e.target.value)}
                          />
                        </FlexRow>
                      </OptionalFormSection>
                      <div
                        className={`${
                          seeMoreFields ? 'mt-5' : 'mt-0'
                        } text-sm cursor-pointer opacity-60 hover:opacity-100 transition duration-300`}
                        onClick={() => setSeeMoreFields((s) => !s)}
                      >
                        {seeMoreFields ? (
                          <div>
                            <i className="mr-1 fas fa-caret-square-up"></i> less parameters
                          </div>
                        ) : (
                          <div>
                            <i className="mr-1 fas fa-caret-square-down"></i> more parameters
                          </div>
                        )}
                      </div>

                      <FlexCenter>
                        <input
                          type="submit"
                          value="Submit"
                          className={
                            'w-52 px-6 pt-3 pb-4 text-base text-center bg-purple-700  ' +
                            ' rounded-lg cursor-pointer lg:transition lg:duration-300 hover:bg-purple-900 text-white'
                          }
                        />
                      </FlexCenter>
                    </form>
                  </FlexCenter>

                  <FlexCenter className="w-full p-5 bg-gray-700 md:p-10 lg:w-1/2 lg:h-full rounded-xl">
                    <Descs activeField={activeField} />
                  </FlexCenter>
                </FlexRow>
              </FlexCol>
            </FlexCenter>
          </FlexCol>
        </Container>
      </Layout>
    );
};

export async function getServerSideProps(context) {
  try {
    const cookies = nookies.get(context);
    const token = await verifyIdToken(cookies.token);
    const { uid, email } = token;
    return {
      props: { email, uid, authed: true },
    };
  } catch (err) {
    nookies.set(context, 'latestPage', '/job', {});
    return {
      redirect: {
        permanent: false,
        destination: '/login',
      },
    };
  }
}

export default Job;
