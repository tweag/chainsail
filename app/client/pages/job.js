import { useState } from 'react';
import nookies from 'nookies';
import {
  Container,
  Dropdown,
  Link,
  Layout,
  FlexRow,
  FlexCol,
  FlexCenter,
  FileFormField,
  FormField,
  MathTex,
  Navbar,
  Modal,
} from '../components';
import getConfig from 'next/config';
const { serverRuntimeConfig } = getConfig();
import firebaseClient from '../utils/firebaseClient';

const JobPageModal = ({ jobId, err, errMsg, isModalActive, setIsModelActive }) => {
  const buttonStyle =
    'px-6 py-2 text-xs md:text-base text-center rounded-lg cursor-pointer lg:transition lg:duration-300  text-white';
  return (
    <Modal isActive={isModalActive}>
      {!err && (
        <>
          <div className="mb-7">
            Job with id {jobId} created successfully. Start it by clicking the button on the "My
            jobs" page.
          </div>
          <FlexCenter>
            <FlexRow className="space-x-10">
              <Link href="/results">
                <a className={buttonStyle + ' bg-purple-700 hover:bg-purple-900'}>
                  View your jobs
                </a>
              </Link>
              <div
                className={buttonStyle + ' bg-gray-700 hover:bg-gray-800'}
                onClick={() => setIsModelActive(false)}
              >
                Create another job
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

const Descs = ({ activeField, seeMoreFields }) => (
  <FlexCol between className="w-full p-5 bg-gray-700 space-y-1 lg:space-y-3 md:p-10 rounded-xl">
    <FieldDescription activeField={activeField} name={['job_name']} icon="fas fa-bars">
      Job name: a unique key id for your job.
    </FieldDescription>
    <FieldDescription
      activeField={activeField}
      name={['num_production_samples', 'num_optimization_samples']}
      icon="fas fa-stream"
    >
      N° production {seeMoreFields ? '/ optimization samples' : ''} : number of MCMC samples in
      production {seeMoreFields ? '/ optimization runs' : ''}
    </FieldDescription>
    <FieldDescription
      activeField={activeField}
      name={['max_replicas', 'initial_number_of_replicas']}
      icon="fas fa-cloud"
    >
      Max {seeMoreFields ? '/ initial' : ''} N° replicas: maximum{' '}
      {seeMoreFields ? '/ initial' : ''} number of replicas to use. The more replicas, the better
      the sampling, but the more compute quota you will use
    </FieldDescription>
    <FieldDescription
      activeField={activeField}
      name={['probability_definition']}
      icon="fas fa-link"
    >
      Probability definition: zip archive including importable Python module providing the
      probability density (max. size: 2 Mb)
    </FieldDescription>
    <FieldDescription activeField={activeField} name={['dependencies']} icon="fas fa-bolt">
      Dependencies: comma-separated list of dependencies to install on compute nodes; see list of
      preinstalled dependencies{' '}
      <a
        target="_blank"
        href="https://github.com/tweag/chainsail-resources/blob/main/documentation/defining_custom_probability.md"
        className="inline text-blue-400 hover:text-white transition duration-300"
        target="_blank"
      >
        here
      </a>
    </FieldDescription>
    {seeMoreFields && (
      <FieldDescription
        activeField={activeField}
        name={['tempered_distribution_family']}
        math="\{\mathbb{P}\}"
      >
        Tempering scheme: the family of tempered distributions Chainsail uses; explanation of
        choices{' '}
        <a
          target="_blank"
          href="https://github.com/tweag/chainsail-resources/blob/main/documentation/algorithms/replica_exchange.md"
          className="inline text-blue-400 hover:text-white transition duration-300"
          target="_blank"
        >
          here
        </a>
        . Note that the likelihood tempering scheme does not support PyMC and Stan interfaces.
      </FieldDescription>
    )}
    {seeMoreFields && (
      <FieldDescription activeField={activeField} name={['minimum_beta']} math="\beta_{min}">
        Beta min: the minimum inverse temperature (beta) which determines the flatness of the
        flattest distribution
      </FieldDescription>
    )}
    {seeMoreFields && (
      <FieldDescription activeField={activeField} name={['target_acceptance_rate']} math="\rho">
        Target acceptance rate: the acceptance rate between neigboring replicas that the algorithm
        aims to achieve. 0.2 is a good value.
      </FieldDescription>
    )}
  </FlexCol>
);

const OptionalFormSection = ({ children, active }) => (
  <FlexCol
    className={`${
      active ? 'h-56 md:h-36' : 'opacity-0 h-0 pointer-events-none'
    } w-full transition-all duration-900 space-y-1`}
  >
    {children}
  </FlexCol>
);

const Job = ({ authed = true, isMobile }) => {
  if (serverRuntimeConfig.require_auth) {
    firebaseClient();
  }

  const [activeField, setActiveField] = useState('other');

  // Form fields state variables
  const [job_name, setJobName] = useState('my_sampling_job');
  const [max_replicas, setMaxReplicas] = useState(20);
  const [initial_number_of_replicas, setInitNReplicas] = useState(5);
  const [tempered_distribution_family, setTemperedDist] = useState('boltzmann');
  const [num_production_samples, setNumProductionSamples] = useState(10000);
  const [num_optimization_samples, setNumOptimizationSamples] = useState(5000);
  const [minimum_beta, setMinBeta] = useState(0.01);
  const [target_acceptance_rate, setTargetAcceptanceRate] = useState(0.2);
  const [probability_definition, setProbDef] = useState(null);
  const [dependencies, setDeps] = useState(['numpy', 'scipy', 'chainsail-helpers']);

  const [createdJobId, setCreatedJobID] = useState(null);

  // Error handling states
  const [err, setErr] = useState(false);
  const [errMsg, setErrMsg] = useState('');

  // See more job form options
  const [seeMoreFields, setSeeMoreFields] = useState(false);

  // Active model state
  const [isModalActive, setIsModelActive] = useState(false);

  const uploadFile = () => {};

  const createJob = async () => {
    const body = {
      name: job_name,
      initial_number_of_replicas:
        seeMoreFields && initial_number_of_replicas
          ? initial_number_of_replicas
          : Math.max(2, Math.floor(max_replicas * 0.25)),
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
            : Math.ceil(Math.floor(num_production_samples * 0.5) / 1000) * 1000,
      },
      optimization_parameters: {
        optimization_quantity_target: target_acceptance_rate,
      },
      dependencies: [{ type: 'pip', deps: dependencies }],
    };

    let data = new FormData();
    for (var key in body) {
      data.append(key, JSON.stringify(body[key]));
    }
    data.append('probability_definition', probability_definition);
    const requestOptions = {
      method: 'POST',
      body: data,
    };

    try {
      let response = await fetch('/api/job/create', requestOptions);
      let data = await response.json();
      if (response.ok && data.job_id) {
        setErr(false);
        setCreatedJobID(data.job_id);
        setIsModelActive(true);
      } else if (data.message) {
        setErr(true);
        setErrMsg(data.message);
        setIsModelActive(true);
      } else {
        setErr(true);
        setErrMsg('Something went wrong. To help us debug, please contact support@chainsail.io.');
        console.log(data);
        setIsModelActive(true);
      }
    } catch (e) {
      setErr(true);
      setErrMsg(
        'Something went wrong. To help us debug, please contact support@chainsail.io.' +
          (e.message ? ` Error: ${e.message}` : '') // Error object have a .message property containing the full message
      );
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
        <FlexCol className="min-h-screen text-white bg-gradient-to-r from-purple-900 to-indigo-600 font-body">
          <Navbar isMobile={isMobile} />
          <Container>
            <FlexCenter className="w-full h-full py-5 md:py-20">
              <FlexCol center className="w-full h-full">
                <div className="mb-10 text-2xl md:text-5xl lg:text-6xl">
                  Create a sampling job
                  <i className="ml-3 fas fa-rocket"></i>
                </div>
                <FlexCol
                  between
                  className="w-full mb-10 text-base md:text-xl lg:w-2/3 md:text-justify"
                >
                  <div>
                    Run Chainsail with an ready-made density (download an{' '}
                    <a
                      target="_blank"
                      href="https://storage.googleapis.com/resaas-dev-public/mixture.zip"
                      className="inline text-blue-400 hover:text-white transition duration-300"
                      target="_blank"
                    >
                      example
                    </a>
                    ) or define your own probability! To do that, use the probability density
                    function (PDF) interfaces provided in the{' '}
                    <a
                      target="_blank"
                      href="https://github.com/tweag/chainsail-resources/blob/main/chainsail_helpers"
                      className="inline text-blue-400 hover:text-white transition duration-300"
                      target="_blank"
                    >
                      chainsail-helpers
                    </a>{' '}
                    Python package.
                  </div>
                  <div>
                    The{' '}
                    <a
                      target="_blank"
                      href="https://github.com/tweag/chainsail-resources"
                      className="inline text-blue-400 hover:text-white transition duration-300"
                    >
                      chainsail-resources
                    </a>{' '}
                    repository contains examples for PDFs defined from scratch, using PyMC3 and
                    Stan. There you'll also find a{' '}
                    <a
                      href="https://github.com/tweag/chainsail-resources/blob/main/documentation/parameters.md"
                      className="inline text-blue-400 hover:text-white transition duration-300"
                      target="_blank"
                    >
                      detailed explanation
                    </a>{' '}
                    of all job parameters.
                  </div>
                </FlexCol>
                <FlexCol
                  between
                  className="w-full mb-10 text-base md:text-xl lg:w-2/3 md:text-justify"
                >
                  <div>
                    You can extract the samples from your distribution from the downloaded results
                    by using the{' '}
                    <a
                      href="https://github.com/tweag/chainsail-resources/tree/main/chainsail_helpers/chainsail_helpers/scripts"
                      className="inline text-blue-400 hover:text-white transition duration-300"
                      target="_blank"
                    >
                      concatenate-samples script
                    </a>{' '}
                    provided in the chainsail-helpers package.
                  </div>
                </FlexCol>
                <FlexRow
                  between
                  responsive
                  media="lg"
                  className={`${
                    seeMoreFields ? 'space-y-28' : ''
                  } w-full lg:space-y-0 lg:h-4/5 lg:space-x-10`}
                >
                  <FlexCenter className="flex-grow mb-10 lg:py-10 h-96 md:h-80 lg:h-full lg:mb-0 lg:w-1/2">
                    <form
                      className="h-full"
                      onSubmit={(e) => {
                        e.preventDefault();
                        if (!isModalActive) createJob(e);
                      }}
                    >
                      <FlexCol between className="mb-1 space-y-1">
                        <FormField
                          label="Job name"
                          inputName="job_name"
                          setActiveField={setActiveField}
                          value={job_name}
                          onChange={(e) => setJobName(e.target.value)}
                        />
                        <FormField
                          label="N° production samples"
                          inputName="num_production_samples"
                          inputType="number"
                          setActiveField={setActiveField}
                          minNumber={1000}
                          maxNumber={50000}
                          stepNumber={1000}
                          value={num_production_samples}
                          onChange={(e) => setNumProductionSamples(e.target.value)}
                        />
                        <FormField
                          label="Max N° replicas"
                          inputName="max_replicas"
                          inputType="number"
                          setActiveField={setActiveField}
                          minNumber={2}
                          maxNumber={20}
                          value={max_replicas}
                          onChange={(e) => setMaxReplicas(e.target.value)}
                        />
                        <FileFormField
                          label="Probability definition (.zip)"
                          inputName="probability_definition"
                          setActiveField={setActiveField}
                          onChange={function (e) {
                            if (e.target.files[0].size > 2097152) {
                              alert('File exceeds maximum size (2 Mb)');
                              e.target.value = '';
                            } else {
                              setProbDef(e.target.files[0]);
                            }
                          }}
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
                          className="space-y-1 md:space-y-0 md:space-x-2"
                        >
                          <FormField
                            optional
                            label="Initial N° replicas"
                            inputName="initial_number_of_replicas"
                            inputType="number"
                            setActiveField={setActiveField}
                            minNumber={2}
                            maxNumber={max_replicas}
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
                            maxNumber={50000}
                            stepNumber={1000}
                            value={num_optimization_samples}
                            onChange={(e) => setNumOptimizationSamples(e.target.value)}
                          />
                        </FlexRow>
                        <Dropdown
                          optional
                          label="Tempering scheme"
                          inputName="tempered_distribution_family"
                          setActiveField={setActiveField}
                          value={tempered_distribution_family}
                          onChange={(e) => setTemperedDist(e.target.value)}
                        />
                        <FlexRow
                          responsive
                          media="md"
                          className="space-y-1 md:space-y-0 md:space-x-2"
                        >
                          <FormField
                            label="Beta min"
                            optional
                            inputName="minimum_beta"
                            inputType="number"
                            setActiveField={setActiveField}
                            minNumber={0.001}
                            maxNumber={1}
                            stepNumber={0.001}
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
                        className="mb-2 text-sm cursor-pointer md:mb-0 opacity-60 hover:opacity-100 transition duration-300"
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
                          value="Create job"
                          className={
                            'w-52 px-6 pt-3 pb-4 text-base text-center bg-purple-700  ' +
                            ' rounded-lg cursor-pointer lg:transition lg:duration-300 hover:bg-purple-900 text-white'
                          }
                        />
                      </FlexCenter>
                    </form>
                  </FlexCenter>

                  <FlexCenter className="w-full lg:w-1/2 duration-300 transition">
                    <Descs activeField={activeField} seeMoreFields={seeMoreFields} />
                  </FlexCenter>
                </FlexRow>
              </FlexCol>
            </FlexCenter>
          </Container>
        </FlexCol>
      </Layout>
    );
};

export async function getServerSideProps(context) {
  try {
    let props;
    if (serverRuntimeConfig.require_auth) {
      const { verifyIdToken } = require('../utils/firebaseAdmin');
      const cookies = nookies.get(context);
      const token = await verifyIdToken(cookies.token);
      const { uid, email } = token;
      props = { email, uid, authed: true };
    } else {
      props = { email: 'jane@doe.com', uid: 'fakeuid', authed: true };
    }
    return { props };
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
